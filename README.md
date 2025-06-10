<h2 align="center">Integrating AI into Clinical Workflows: A Simulation Study on Implementing AI-aided Same-day Diagnostic Testing Following an Abnormal Screening Mammogram

## AMIA 2024 Annual Symposium Paper
## https://pmc.ncbi.nlm.nih.gov/articles/PMC12099379/ 
  
Yannan Lin, MD, MPH, PhD1, Anne C. Hoyt, MD2, Vladimir G. Manuel, MD3,4, Moira Inkelas, MPH, PhD4,5, Cleo K. Maehara1, MD, MMSc, Mehmet Ulvi Saygi Ayvaci, PhD6, Mehmet Eren Ahsen, PhD7,8, William Hsu, PhD1,9

1 Medical & Imaging Informatics, Department of Radiological Sciences, David Geffen School of Medicine at UCLA, Los Angeles, CA, USA; 
2 Department of Radiological Sciences, David Geffen School of Medicine at UCLA, Los Angeles, CA, USA; 
3 Department of Family Medicine, David Geffen School of Medicine at UCLA, Los Angeles, CA, USA; 
4 UCLA Clinical and Translational Science Institute, Los Angeles, CA, USA; 
5 Department of Health Policy and Management, UCLA Fielding School of Public Health, Los Angeles, CA, USA;
6 Naveen Jindal School of Management at the University of Texas at Dallas, Richardson, TX, USA; 
7 Department of Business Administration, Gies College of Business, University of Illinois at Urbana-Champaign, Champaign, IL, USA; 
8 Department of Biomedical and Translational Sciences, Carle Illinois School of Medicine, University of Illinois at UrbanaChampaign, Urbana, IL, USA;
9 Department of Bioengineering, University of California, Los Angeles, CA, USA

## Introduction
Artificial intelligence (AI) shows promise in clinical tasks, yet its integration into workflows remains underexplored. This study proposes an AI-aided same-day diagnostic imaging workup to reduce recall rates following abnormal screening mammograms and alleviate patient anxiety while waiting for the diagnostic examinations. This paper explores different scenarios for implementing an AI-assisted same-day diagnostic workup workflow in a breast imaging center using discrete event simulation (DES). It examines various options for the timing of the AI-assisted workflow—whether it operates continuously throughout the day, only in the morning, or only in the afternoon. Additionally, it considers the allocation of radiologists, such as assigning specific radiologists to handle particular types of cases, like screening mammograms combined with same-day diagnostic workups. The supplemental materials of the paper is titled Supplemental Material_v20240812.docx in this repo. 

Workflow:
![Figure 1](https://github.com/user-attachments/assets/4c5dc901-b462-4bcd-8f1d-c8bfb9997dbc)

## Steps to run the simulation models

### Step 1 - Code download
Download the ./code folder to your local machine.

### Step 2 - Requirements
Install all required packages listed in ./code/requirements.txt file

### Step 3 - Command Line Commands for baseline workflow
Locate the ./code folder and run the following command.

`python run_simulation.py`

By default, the simulation runs the baseline workflow without the AI-aided same-day diagnostic workups with num_interation=10, ai_time='none', rad_change=False, and rad_change_2=Fasle.

### Step 4 - Command Line Commands for AI-aided same-day diagnostic workflow

An example of the AI-aided workflow with AI running in the morning, dedicating one radiologist to screening mammogramphy + same-day diagnostic exams, and no radiologist to screening mammogramphy + same-day diagnostic exams + regular diagnostic exams. 

`python run_simulation.py --wf_1ss True --ai_time morning --rad_change True --rad_change_2 False`

An example of the AI-aided workflow with AI running in the afternoon, dedicating no radiologist to screening mammogramphy + same-day diagnostic exams, and no radiologist to screening mammogramphy + same-day diagnostic exams + regular diagnostic exams. 

`python run_simulation.py --wf_1ss True --ai_time afternoon`

The following is a list of parameters to explore.

> wf_1ss: Whether the baseline (False) or AI-aided same-day diagnostics (True) workflow
> 
> ai_time: Time of day for the AI-aided same-day diagnostic workup, choices=['morning', 'afternoon', 'any', 'none']
> 
> rad_change: Dedicate one radilogist to screening mammogramphy + same-day diagnostic exams (True or False)
> 
> rad_change_2: When rad_change is True, rad_change_2 means dedicating one radiologst to screening mammogramphy + same-day diagnostic exams + regular diagnostic exams: True or False')

### Step 4 - Output and post-simulation analysis

The output of the simulation will be saved in the ./code/output/ folder. Each patient and the timestamp of each step are logged for post-simuluation analysis. The two workflows are logged separately. An example of the output file is as follows. The columns in the output file logs the timestamp for each step and waiting times inbetween steps. The lengty of stay in the clinic can be calculdated using (exit_system_ts-arrival_ts). Each output file stores inforamation of one simulated clinic day. 

<img width="867" alt="Screenshot 2024-09-01 at 8 51 16 PM" src="https://github.com/user-attachments/assets/d14d5ffd-d730-4466-b43b-44241d096a3c">

### Workflow Customization

The user may customize this code for their own workflow simulation with different model paramters. They may modify the values in the following input files.
1. ./data/exam_percent_BK_22_12.csv stores the proportion of exams for each hour. E.g., exam_type_new='Bx Mammo', h_7=0, there are 0% stereotactic-guided biopsy from 7 am to 8 am.
2. ./data/num_pt_per_hour_BK_22_12.csv stores the average number of patients per hour. E.g., hour=7, avg=6.09 means from 7 am to 8 am, there are on average 6.09 patients. 

### Notes
1. To change the number of clinic days of the simulation to, for example 100, use: --num_iteration=100
2. When wf_1ss is False (no AI-aided same-day diagnostic workflow), ai_time must be 'none'.
3. wf_1ss must be True for any AI-aided workflow
4. If wf_1ss is False (baseline workflow), rad_change and rad_change_2 can not be True as they are only for the AI-aided workflow
5. In order for rad_change_2 to be True, rad_change needs to be True.
6. 'code' contains the process-oriented version of the simulation, while 'code_oop' contains the object-oriented version.






