import sys
import subprocess


# This turns text numbers from time/perf into Python numbers.
def number(text):
    text = text.strip()
    text = text.replace(",", "")
    return float(text)


# time gives wall time in hour format this changes that to seconds
def wall_seconds(text):
    text = text.strip()

    if ":" not in text:
        return number(text)

    parts = text.split(":")

    if len(parts) == 2:
        return float(parts[0]) * 60 + float(parts[1])

    if len(parts) == 3:
        return float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])


# uses time to get wall time, user time, system time, and major page faults.
def get_time(command):
    user = 0
    sys_time = 0
    wall = 0
    major_page_faults = 0

    output = subprocess.run(
        ["/usr/bin/time", "-v"] + command,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    for line in output.stderr.splitlines():
        line = line.strip()

        if line.startswith("User time"):
            user = number(line.split(":", 1)[1])

        if line.startswith("System time"):
            sys_time = number(line.split(":", 1)[1])

        if line.startswith("Elapsed"):
            wall = wall_seconds(line.split("):", 1)[1])

        if line.startswith("Major"):
            major_page_faults = number(line.split(":", 1)[1])
		
    cpu_ratio = (user + sys_time) / wall

    return user, sys_time, wall, cpu_ratio, major_page_faults


# This runs the program using perf stat.
def get_perf(command):
    cycles = None
    instructions = None
    cache_refs = None
    cache_misses = None

    output = subprocess.run(
        ["perf", "stat", "-e", "cycles,instructions,cache-references,cache-misses"] + command,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    for line in output.stderr.splitlines():
        parts = line.strip().split()

        if len(parts) >= 2:
            name = parts[1]

            if name == "cycles":
                cycles = number(parts[0])

            if name == "instructions":
                instructions = number(parts[0])

            if name == "cache-references":
                cache_refs = number(parts[0])

            if name == "cache-misses":
                cache_misses = number(parts[0])

    ipc = instructions / cycles
    cache_miss_rate = cache_misses / cache_refs

    return ipc, cache_miss_rate

def main():
    command = sys.argv[1:]

    user, sys_time, wall, cpu_ratio, major_page_faults = get_time(command)
    ipc, cache_miss_rate = get_perf(command)

    print()
    print("Measurements")
    print("------------")
    print("Wall time:", wall, "seconds")
    print("User time:", user, "seconds")
    print("System time:", sys_time, "seconds")
    print("CPU/wall ratio:", cpu_ratio)
    print("Major page faults:", major_page_faults)
    print("IPC:", ipc)
    print("Cache miss rate:", cache_miss_rate)
    print()

    print("Possible problems")
    print("-----------------")

    if cpu_ratio >= 0.8:
        print("- CPU time was close to wall time. The CPU appears to be working for most of the elapsed time. ")
        print("  Check for expensive loops.")
        print()

    if cpu_ratio < 0.6:
        print("- CPU time is much smaller than wall time. The program appears to be waiting for most of the elapsed time. ")
        print("  Check file access, sleeps, network access or other I/O.")
        print()

    total_cpu = user + sys_time

    if sys_time / total_cpu > 0.3:
        print("- System time is quite high. A large fraction of CPU time was spent in system/kernel code. ")
        print("Check for excessive printing, file operations, or many small system calls.")
        print()

    if major_page_faults > 0:
        print("- Major page faults occurred. Some memory pages may have had to be fetched from disk rather than already being in RAM.")
        print("  This may suggest high memory use or disk related delays")

    if ipc < 0.8:
        print("- The CPU is doing less than one instruction per cycle on average. IPC is low.")
        print("  This could suggest stalls, cache misses, or interpreter overhead.")
        print()

    if cache_miss_rate > 0.05:
        print("- More than 5 percent of cache references missed. Cache miss rate is high.")
        print("  This may suggest poor locality or poor data reuse. Try using more contiguous data or changing loop order.")
        print()


main()