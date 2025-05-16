import copy
from collections import deque

class AC3:
    def __init__(self, courses, cid_constraints, session_constraints=None ,no_class_constraints=None):
        """
        :courses: List[Course] (must have .id and .name)
        :cid_constraints: dict course_id -> list of timeslot strings
        :session_constraints: List[Course] that the user pre-selected
        """
        self.courses = courses
        self.cid_constraints = cid_constraints
        self.constraints_from_session = session_constraints or []
        self.no_class = no_class_constraints or []
        self.progress = []  # Collecting progress for debugging
        self.domains = {}

        # Debug: print cid_constraints when initializing
        print("DEBUG [AC3 - cid_constraints initialized]:")
        for course_id, timeslots in self.cid_constraints.items():
            print(f"  - Course ID {course_id}: {timeslots}")
        
        self._init_domains()
        self._init_queue()

    def _init_domains(self):
        """
        Initialize domains by iterating over cid_constraints:
          • Honor user picks (unless they conflict with no_class)
          • Then fill in all other IDs, skipping forbidden slots
        """
        raw = {}
        forbidden = {f"{day} {time}" for day, time in self.no_class}

       # 1) Lock in user picks by ID, using cid_constraints to check slots
        skipped_picks = []
        for c in self.constraints_from_session:
            cid = c.id
            info = self.cid_constraints.get(cid)
            if not info:
                continue
            # if any of this CID’s slots conflict, skip entirely
            if all(slot not in forbidden for slot in info['constraints']):
                raw.setdefault(info['course_name'], set()).add(cid)
            else:
                skipped_picks.append(f"{cid}")

        if skipped_picks:
            self.progress.append(
                f"Skipped picked {', '.join(skipped_picks)} due to no-class constraint"
        )


        # 2) Fill in all other IDs from cid_constraints, grouped by course_name
        for cid, info in self.cid_constraints.items():
            name = info['course_name']
            # if user already locked in this variable, skip
            if name in raw:
                continue

            allowed = set()
            pruned = []

            for cid_, detail in self.cid_constraints.items():
                if detail['course_name'] != name:
                    continue
                if all(slot not in forbidden for slot in detail['constraints']):
                    allowed.add(cid_)
                else:
                    pruned.append(cid_)

            if pruned:
                self.progress.append(
                    f"Pruned {', '.join(pruned)} from {name} due to no-class constraint"
                )

            raw[name] = allowed


        # 3) Sort by domain size and convert to lists
        sorted_items = sorted(raw.items(), key=lambda kv: len(kv[1]))
        self.domains = {name: list(ids) for name, ids in sorted_items}

        # DEBUG
        print("DEBUG [AC3 - Domains initialized]:")
        for name, dom in self.domains.items():
            print(f"  - {name}: {dom}")
        self.progress.append(
            "Domains initialized: " +
            ", ".join(f"{n}({len(d)})" for n, d in self.domains.items())
        )

    def _init_queue(self):
        """
        Initialize the queue of arcs to be processed by the AC-3 algorithm.
        """
        vars_ = list(self.domains)
        self.queue = deque((Xi, Xj) for Xi in vars_ for Xj in vars_ if Xi != Xj)
        self.progress.append(f"Queue initialized with {len(self.queue)} arcs")

    def _no_conflict(self, a, b):
        """
        Checks if two course IDs (a, b) have conflicting timeslots.
        Returns True if there is no conflict, and False if there is a conflict.
        """
        # Debug: print the course ids and their corresponding timeslots
        print(f"DEBUG [AC3 - Checking conflict] - Course {a} vs Course {b}:")
        print(f"  - Course {a} Timeslots: {self.cid_constraints[a]['constraints']}")
        print(f"  - Course {b} Timeslots: {self.cid_constraints[b]['constraints']}")

        # Iterate over the timeslots for both courses a and b
        for con in self.cid_constraints[a]['constraints']:
            for con2 in self.cid_constraints[b]['constraints']:
                if con == con2:  # If timeslots conflict
                    self.progress.append(f"Conflict detected: Course {a} and Course {b} have overlapping timeslot {con}")
                    return False  # There is a conflict
        return True  # No conflict found


    def revise(self, Xi, Xj):
        pruned = False
        newdom = []
        
        # Debug: print the domains being revised
        print(f"DEBUG [AC3 - Revising] - Revising domain for {Xi} (Current domain: {self.domains[Xi]})")
        
        for vi in self.domains[Xi]:
            # Keep vi if there's some vj in Xj that doesn't conflict
            if any(self._no_conflict(vi, vj) for vj in self.domains[Xj]):
                newdom.append(vi)
            else:
                pruned = True
                self.progress.append(f"Pruned {vi} from {Xi} (no support in {Xj})")
        
        if pruned:
            self.domains[Xi] = newdom
        return pruned


    def run(self):
        """
        Perform the AC-3 algorithm, pruning the domains of the variables.
        """
        # Debug: before pruning
        self.progress.append(f"DEBUG - Domains before pruning: {self.domains}")

        while self.queue:
            Xi, Xj = self.queue.popleft()
            if self.revise(Xi, Xj):
                # re-enqueue affected arcs
                for Xk in self.domains:
                    if Xk not in (Xi, Xj):
                        self.queue.append((Xk, Xi))

        # Debug: after pruning
        self.progress.append(f"DEBUG - Domains after pruning: {self.domains}")
        self.progress.append("AC-3 done.")
        return self.progress

   

    def _is_consistent(self, assignment, vars_):
        seen = set()
        for var in vars_:
            cid = assignment.get(var)  # Get the course ID corresponding to the course_name
            if cid is None:
                continue
            for slot in self.cid_constraints[cid]["constraints"]:
                if slot in seen:
                    return False
                seen.add(slot)
        return True




    def solve(self):
        """
        Run AC-3, then perform depth-first backtracking to find all valid assignments.
        Stops after all depth-0 (first variable) values have been used.
        """
        self.run()  # Apply AC-3

        # Remove empty domains
        self.domains = {k: v for k, v in self.domains.items() if v}
        if not self.domains:
            return []

        solutions = []
        vars_ = list(self.domains.keys())
        first_var = vars_[0]
        first_domain = self.domains[first_var]


        def backtrack(assignment, depth):
            # If full assignment is found
            if len(assignment) == len(vars_) and self._is_consistent(assignment,vars_) :
                solutions.append(assignment.copy())
                return
            

            var = vars_[depth]
            for val in self.domains[var]:
                assignment[var] = val

                if self._is_consistent(assignment,vars_):
                    backtrack(assignment, depth + 1)

                # Backtrack
                del assignment[var]
            

        # Manually loop over each root value
        for root_val in first_domain:
            assignment = {first_var: root_val}
            backtrack(assignment, 1)

        return solutions


       
        
       
      
