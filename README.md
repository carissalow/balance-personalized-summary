# balance-personalized-report

Personalized data summary reports for participants in the **Behavioral Activation-Led Activity eNgagement for Cancer Empowerment (BALANCE)** study at the Mobile Sensing + Health Institute at the University of Pittsburgh.  

<br>

---

## Installation

1. Install [Miniconda](https://docs.anaconda.com/free/miniconda/miniconda-install/)

2. Install [Quarto](https://quarto.org/docs/get-started/) 

3. Clone the repository:

    ```bash
    git clone https://github.com/jenniferfedor/balance-personalized-summary
    ```

4. Restore the Python virtual environment:

    ```bash
    cd balance-personalized-report
    conda env create -f environment.yml -n balance
    ```

5. Create a `credentials.yaml` file with the following format, filling in the host, user, and password fields:  

    ```yaml
    balance:
        database: "balance"
        host: "[BALANCE study database EC2 instance URL]"
        user: "[BALANCE study database user name]"
        password: "[BALANCE study database user password]"
        port: 3306
    ```

<br>

---

## Execution 

### For a specific participant

To generate a final study report for a **specific** participant, `PID` (e.g., 101), run:

```bash
cd src
conda activate balance
bash render_participant_report.sh PID
```

<br>

### For all participants

To generate final study reports for **all** participants, run: 

```bash
cd src
conda activate balance
bash render_all_reports.sh
```

<br>

---

## Output

Rendered participant-specific reports can be found in `output/balance_final_report_[PID].html`.    

<br>
