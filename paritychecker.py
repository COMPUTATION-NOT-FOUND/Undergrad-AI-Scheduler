import pandas as pd
import ast

def parse_solutions(filepath):
    df = pd.read_csv(filepath)
    df = df.dropna(how='all')
    sols = {}
    for _, row in df.iterrows():
        key = row['Solution']
        cid = int(row['id'])
        slots = tuple(ast.literal_eval(row['constraints']))
        sols.setdefault(key, []).append((cid, slots))
    return sols

def canonicalize(solution_courses):
    return frozenset(solution_courses)

def compare_solution_sets(file_a, file_b, out_path="comparison.txt"):
    sols_a = parse_solutions(file_a)
    sols_b = parse_solutions(file_b)
    set_a = {canonicalize(c) for c in sols_a.values()}
    set_b = {canonicalize(c) for c in sols_b.values()}
    only_a = set_a - set_b
    only_b = set_b - set_a
    both   = set_a & set_b

    # 1) Build the full report in memory
    report_lines = []

    def build_section(sol_set, title):
        report_lines.append(f"=== {title} ({len(sol_set)} solutions) ===")
        for sol in sol_set:
            for cid, slots in sorted(sol):
                report_lines.append(f"{cid}: {list(slots)}")
            report_lines.append("-" * 40)
        report_lines.append("")  # blank line

    build_section(only_a, "Only in File A")
    build_section(only_b, "Only in File B")
    build_section(both,   "In Both Files")

    # 2) Write it all to disk
    with open(out_path, "w") as fout:
        fout.write("\n".join(report_lines))

    # 3) Print a concise console summary
    print(f"\nFull comparison written to {out_path}\n")
    print(f"Only in A: {len(only_a)} solutions")
    print(f"Only in B: {len(only_b)} solutions")
    print(f"In Both: {len(both)} solutions\n")

    # Show the first few lines of each section as a sanity check
    def tail_preview(lines, title, count=3):
        print(f"--- {title} (showing up to {count} sols) ---")
        section = []
        collecting = False
        sols_shown = 0
        for line in lines:
            if line.startswith(f"=== {title}"):
                collecting = True
                continue
            if line.startswith("===") and collecting:
                break
            if collecting and line and not line.startswith("-"):
                print(line)
                sols_shown += 1
                if sols_shown >= count:
                    break
        print()

    tail_preview(report_lines, "Only in File A")
    tail_preview(report_lines, "Only in File B")
    tail_preview(report_lines, "In Both Files")

if __name__ == "__main__":
    compare_solution_sets(
        "generated_schedules.csv",
        "benchmarks/AC3/generated_schedules.csv",
        out_path="comparison.txt"
    )
