import subprocess

scripts = ["tracker.py", "data_processing.py", "visualize_scores.py"]

for script in scripts:
    print(f"Running {script}...")
    try:
        subprocess.run(["python", script], check=True)
    except KeyboardInterrupt:
        print(f"\n{script} was interrupted manually with CTRL+C.")
        print("Continuing to the next script...\n")
    except subprocess.CalledProcessError as e:
        print(f"{script} failed with exit code {e.returncode}. Stopping.")
        break
    else:
        print(f"{script} completed successfully.\n")
