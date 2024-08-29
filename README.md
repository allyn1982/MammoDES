<h2 align="center">Integrating AI into Clinical Workflows: A Simulation Study on Implementing AI-aided Same-day Diagnostic Testing Following an Abnormal Screening Mammogram

## AMIA 2024 Annual Symposium Paper
  
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
Artificial intelligence (AI) shows promise in clinical tasks, yet its integration into workflows remains underexplored. This study proposes an AI-aided same-day diagnostic imaging workup to reduce recall rates following abnormal screening mammograms and alleviate patient anxiety while waiting for the diagnostic examinations. This paper explores different scenarios for implementing an AI-assisted same-day diagnostic workup workflow in a breast imaging center. It examines various options for the timing of the AI-assisted workflow—whether it operates continuously throughout the day, only in the morning, or only in the afternoon. Additionally, it considers the allocation of radiologists, such as assigning specific radiologists to handle particular types of cases, like screening mammograms combined with same-day diagnostic workups. 

A simplified version of the workflows has been published: https://pubmed.ncbi.nlm.nih.gov/38827101/ 
![2241f1](https://github.com/user-attachments/assets/41eb5223-42db-49a8-a6c0-f44ee47369d7)

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

`python run_simulation.py --wf_1ss True --ai_time monring --rad_change True --rad_change_2 False`

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

### Notes
1. To change the number of clinic days of the simulation to, for example 100, use: --num_iteration=100
2. When wf_1ss is False (no AI-aided same-day diagnostic workflow), ai_time must be 'none'.
3. wf_1ss must be True for any AI-aided workflow
4. If wf_1ss is False (baseline workflow), rad_change and rad_change_2 can not be True as they are only for the AI-aided workflow
5. In order for rad_change_2 to be True, rad_change needs to be True.






