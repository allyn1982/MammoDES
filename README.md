# Integrating AI into Clinical Workflows: A Simulation Study on Implementing AI-aided Same-day Diagnostic Testing Following an Abnormal Screening Mammogram

## AMIA 2024 Annual Symposium Paper

## Steps to run the simulation 
The paper investigates various scenarios of implementing an AI-aided same-day diagnostic workup workflow in a breast imaging center, including varying the time AI-aided workflow runs and the allocation of radiologists. 

### Step 1 - Requirements
Install all required packages listed in ./code/requirements.txt file

### Step 2 - Command Line Commands
'python run_simulation.py'
By default, the simulation runs the baseline workflow without the AI-aided same-day diagnostic workups with num_interation=10, ai_time='none', rad_change=False, and rad_change_2=Fasle.
num_iteration: the number of clinic days to simulate (max=1000)
wf_1ss: Whether the baseline (False) or AI-aided same-day diagnostics (True) workflow
ai_time: Time of day for the AI-aided same-day diagnostic workup, choices=['morning', 'afternoon', 'any', 'none']
rad_change: Dedicate one radilogist to screening mammogramphy + same-day diagnostic exams (True or False)
rad_change_2: When rad_change is True, rad_change_2 means dedicating one radiologst to screening mammogramphy + same-day diagnostic exams: True or False')




