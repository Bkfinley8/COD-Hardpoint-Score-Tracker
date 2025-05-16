import subprocess

def run_scripts():
    try:
        print("Running data_cleansing.py...")
        subprocess.run(["python", "data_cleansing.py"], check=True)

        print("Running visualize_scores_styled.py...")
        subprocess.run(["python", "visualize_scores_styled.py"], check=True)

        print("Both scripts executed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while executing {e.cmd}:")
        print(e)

if __name__ == "__main__":
    run_scripts()