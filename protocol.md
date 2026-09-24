## Project Summary & Objective

The overarching goal of this research is to develop safer, more reliable large language models (LLMs) by understanding how humans navigate ambiguity through multi-turn clarifying dialogs. In this study, we will characterize how humans ask and answer clarifying questions when provided with multimodal context, such as text, images, and audio. Participants will use a secure web platform to contribute to ongoing conversation histories, acting as both a "question asker" or "question answerer" to provide the next logical response dialogs. These data will be used to investigate the distribution of types of questions humans ask, measure how many dialog turns it takes to converge on a fully disambiguated answer, and observe human responses to common LLM conversational failures, such as reward hacking. By establishing a robust dataset of verified, human-driven multi-turn dialogs, this study seeks to create a new benchmark for evaluating and training AI systems, ultimately improving their ability to safely and effectively process complex, underspecified real-world requests.

## Motivation & Background

The motivating objective of this study is to create safer large language models by understanding how humans operate under ambiguity and creating a benchmark that language models must pass to be considered equal to humans in ability to disambiguate. People are increasingly relying on large language models to perform complex tasks requiring intricate understanding of the object and details of a request. Human requests often underspecify objectives or details which can cause multiple contradictory outcomes of the request to be equally valid. Current open source language models tend to make assumptions about underspecified information early in conversations which then causes them to end the conversation early with an incorrect outcome \[1\].

Underspecified information can be disambiguated through the use of clarifying dialogs which consist of the original ambiguous request and one or more rounds of clarifying questions and answers. A clarifying dialog with a single clarifying question and answer is called a single-turn clarifying dialog while a dialog with multiple clarifying questions and answers in sequence is called a multi-turn clarifying dialog. Current methods that train large language models to engage in clarifying dialogs have one or more of the following limitations:

1. Models are trained to engage in only single turn dialogs \[2, 3\]. For complex requests where multiple pieces of information are underspecified, a single turn is incapable of disambiguating the entire request. Ongoing research in the Corso Group has shown that models trained to engage in single turn dialogs fails to generalize to multi-turn dialogs.  
2. Datasets are generated via means that have not been verified to create reasonably human-like dialogs. These consist of using large language models to generate ground truth clarifying questions \[2, 1\], or concatenating single-turn dialogs into multi-turn dialogs \[4\]. These datasets can be used to train models capable of engaging in multi-turn dialogs in theory, but there is no verification that these models perform well when in dialog with humans.  
3. Datasets are too small to be used for statistical analysis or model training. The prevalence of the above limitations can be attributed to the fact that general multi-turn dialog datasets are rare and small and that detecting ambiguity inside such datasets can be difficult. This causes datasets to be small and highly specific to a given task \[3\].

By using a website to allow participants to quickly and asynchronously engage in multi-turn dialogs with other participants, we are directly addressing these limitations. We collect real, multi-turn clarifying dialogs by having participants act as both the character of clarifying question asker and clarifying question answerer and ensure large sample count by having participants contribute to multiple ongoing dialogs, removing the need to pause and wait for another participant to respond. The data collected from this study will allow researchers to analyze the ability of their models to create clarifying questions within the distribution of human clarifying questions and will be used to directly train models that are capable of engaging in human-like multi-turn clarifying dialogs.

\[1\] K. Ramezan, A. A. Bavandpour, Y. Yuan, C. Siro, and M. Aliannejadi, ‘Multi-Turn Multi-Modal Question Clarification for Enhanced Conversational Understanding’, arXiv \[cs.IR\]. 2025\.  
[https://arxiv.org/abs/2505.06120](https://arxiv.org/abs/2505.06120)  
\[2\] P. Jian, D. Yu, W. Yang, S. Ren, and J. Zhang, ‘Teaching Vision-Language Models to Ask: Resolving Ambiguity in Visual Questions’, arXiv \[cs.CV\]. 2025\. [https://arxiv.org/abs/2507.13773](https://arxiv.org/abs/2507.13773)  
\[3\] E. Stengel-Eskin, J. Guallar-Blasco, Y. Zhou, and B. Van Durme, ‘Why Did the Chicken Cross the Road? Rephrasing and Analyzing Ambiguous Questions in VQA’, arXiv \[cs.CL\]. 2023\. [https://arxiv.org/abs/2211.07516](https://arxiv.org/abs/2211.07516)   
\[4\] P. Laban, H. Hayashi, Y. Zhou, and J. Neville, ‘LLMs Get Lost In Multi-Turn Conversation’, arXiv \[cs.CL\]. 2025\. [https://arxiv.org/abs/2502.11442](https://arxiv.org/abs/2502.11442)

## Study Population

The study population is people affiliated with the University of Michigan that have a [umich.edu](http://umich.edu) email address and are of the age of 18 or older.

### Recruitment Strategy

Participants will be recruited through UMHealthResearch, student slack groups, direct emails, listservs, and the UMich Targeted Email Service. Potential participants will fill out a qualtrics survey which will collect name, demographic information, and a [umich.edu](http://umich.edu) email address. If they meet the eligibility criteria, they will be automatically emailed a link to the study website along with a random id that they enter to access the study page.

### Eligibility Criteria

In order to ensure that the study population aligns with the population that open source large language models are intended to interact with, participants must meet the following criteria:

- Fluent in english  
- No visual or hearing impairment  
- Umich affiliated (has [umich.edu](http://umich.edu) email)

## Study Design

The study is conducted from home using a secure website to perform data entry. The participants will engage in one of two tasks. For both tasks, they will see a history of a conversation consisting of clarifying questions and answers to those clarifying questions and be prompted to enter the next response in that conversation. Previous statements in the conversation are either sourced from other participants or a multi-modal large language model.

### Website Hosting

The website and associated backend will be hosted on a secure server locked in a data center on north campus that only certain individuals have access to. All data collected from the website will be stored on the lab computer and backed up periodically to dropbox.

### Access control

When the user first opens the website they are presented with an access control screen that has the title of the study and a text field that allows them to enter their login id which was emailed to them with the study invitation, as seen in Figure 1.After entering their login id, if they have not been presented with the consent information, it will present a screen with a PDF of the consent information and a checkbox below that allows them to verify that they have read the consent information (Figure 2).  
Once they have verified that they have read the consent information, subsequent visits to the study site will not present the access control screen or the consent information.![][image1]  
Figure 1: Mockup of access control page of website

![][image2]  
Figure 2: Mockup of consent/information page of website

### Study Page

After passing access control, the participant is directed to the main study page. The participant is shown a multi-modal input (image, sound, etc…) and a dialog history consisting of a conversation between the clarifying question asker and the clarifying question answerer. Depending on whether the participant performing the Clarifying Question Asker Task or the Clarifying Question Answerer Task, they will be shown a different response form. Which task a participant will perform next will depend on prior participant responses.

#### Clarifying Question Asker Task

The question asker will be presented with the instruction defined in section \[FILL IN Question Asker Instruction section\] of the appendix.  
The question asker will be asked to fill in the following:

1. Whether they think the previous clarifying answer is meaningful in context.  
2. Their current guess as to what the answer to the initial ambiguous question is.  
   1. An accompanying Likert scale that gauges how confident they are about their answer.  
3. The next clarifying question they wish to ask.

If there are no previous clarifying questions and answers in the presented dialog, the participant will be presented with only the multi-modal input and an ambiguous question and must ask the first clarifying question. The initial multi-modal input and ambiguous question is sourced from external datasets.

![][image3]  
Figure 3: Example structure for the Clarifying Question Asker task page

#### Clarifying Question Answerer Task

The question answerer will be presented with the instruction defined in section \[FILL IN Question Answerer Instructions sectio\] of the appendix.  
The question answerer will be given the additional pieces of information:

1. The intended unambiguous question that is the pair of the ambiguous question that begins the dialog.

The question answerer will be asked to fill in the following:

1. A Likert rating for how relevant they think the previous clarifying question is.  
2. A Likert rating for how informative they think the previous clarifying question is.  
3. The answer to the previous clarifying question.

![][image4]  
Figure 4: Example structure for the Clarifying Question Answerer task page

### Participation Phases

The study is divided into two phases. The tasks are identical between the two phases, but some participants will not be invited to participate in Phase 2 based on quantitative statistics of their responses in Phase 1\.

#### Phase 1

We consider this a trial period where we collect statistics such as response frequency and moderation flag rate. Phase 1 lasts until the participant contributes N responses. Collected responses are saved and used for analysis, but if the participant does not meet the criteria they are not invited to participate in phase 2\.

#### Phase 2

For individuals that met the criteria, we invite them to continue entering answers for a total of at most N responses.

### Moderation

Since users will be responding to inputs from another character (either another participant or a language model), there is the potential for harmful speech to be submitted. We will have a two stage approach to prevent such harmful speech from being shown to participants.

#### Automated moderation

Submitted responses will be processed by an automated moderation tool. This will flag classes such as obscenity, threats, insults, identity attacks, and sexual content. Responses that are not flagged under any of these categories will not be reviewed further and will be allowed to be presented to participants. If a response is flagged by automated moderation, a further review by a human moderator will be conducted.

#### Human moderation

If a response is flagged by the automated moderation tool then we put the response on hold (will not be shown to any other humans). We put the response into a queue to be reviewed by a human moderator. If the human disagrees with the automated moderator, the response is put back into the pool and can be shown to human participants. If the human agrees with the automated moderator, the response is removed from the pool, but is still saved in our database.

## Risks and Benefits

The participants will not receive any personal benefits for participating in the study. However, others may benefit from the knowledge gained from their participation. Study results may lead to increased safety of large language model systems by reducing the tendency of models to make incorrect assumptions leading to useless or harmful results.

Participants may be exposed to harmful speech entered by other participants. To mitigate this, we will use automated moderation tools running locally on the server on north campus to flag potentially harmful speech. Any speech that is flagged as potentially harmful will not be shown to a participant until it is reviewed by a human. In case the auto moderation tool fails to flag harmful speech, participants will be given the opportunity to flag any part of a dialog for review, in which case that dialog will not be shown to a new participant until it is reviewed by a human moderator.

Participants may be uncomfortable responding to a dialog. In this case, they are free to opt to skip giving a response and move on to the next response or exit the website.

Participants may be at risk of loss of confidentiality of their private information gathered during  
this study. To mitigate any potential harm from loss of confidentiality, we will collect the minimal personal identifying information necessary to compensate participants. The research team will follow the data storage procedures of Section \[FILL IN Data Management section number\] to mitigate the potential risk associated with loss of confidentiality.

## Data Management

All data collected from the website will be stored on a secure server located on north campus that hosts the website. It will periodically be backed up to a dropbox that only the study team will have access to. All data stored on the lab computer will refer to participants using a random unique identifier. A link sheet to allow identification given a unique identifier will be stored on dropbox for the purpose of compensation and will be destroyed after the study concludes.

De-identified data will be used to train language models capable of asking and answering clarifying questions. The weights for this model will be released as accessible and modifiable by anyone. We will also release the de-identified data as an open access dataset.

## Compensation

Participants will be compensated for completing study activities in the phase in which they are  
enrolled. Compensation procedures will follow the University’s HSIP guidelines. Gift cards will  
be requested through the official HSIP process by the study team and mailed to participants after completion of their study participation or withdrawal from the study.

The compensation that can be received by a participant in Phase 1 is $\[FILL IN\] for entering \[FILL IN\] responses. The maximum compensation that can be received by a participant in Phase 2 is $\[FILL IN\]. Compensation will be pro-rated for Phase 2 based on the number of responses entered. For every \[FILL IN\] responses the participant contributes, they are compensated $\[FILL IN\].

### Ending Participation

If a participant is not invited to phase 2, contributes the maximum allowed responses, or opts to cease participation, their login id will be deactivated and the participant will be compensated for the amount of responses they have contributed.

## Appendices

### Question Asker Instructions

*Note: This will appear as an overlay before the first time a participant is assigned to respond with a clarifying question so that the participant must read it. For subsequent responses, it will appear below the response entry form.*

You are the Question Asker, an investigator. Your goal is to figure out the exact answer to the original ambiguous question by looking at the provided images, audio, or text, and reading the conversation history.

Your Tasks for this Round:

* Evaluate the previous answer: Indicate whether the last response provided by the Answerer made sense and was helpful.  
* Make your best guess: Write down what you currently think the final answer to the original question is, based on the clues you have so far.  
* Rate your confidence: Use the scale to indicate how sure you are about your guess.  
* Ask the next question: Write one single, clear follow-up question that will help you eliminate missing information and get closer to the final answer. Do not ask multiple questions at once.

### Question Answerer Instructions

*Note: This will appear as an overlay before the first time a participant is assigned to respond to a clarifying question so that the participant must read it. For subsequent responses, it will appear below the response entry form.*

You are the Question Answerer, an information source. You are shown the hidden truth that the Question Asker is trying to figure out. You will be shown the "Intended Question," which reveals exactly what the original ambiguous request was actually about.

Your Tasks for this Round:

* Review the hidden truth: Read the Intended Question carefully. Keep this information in mind, but do not give it away for free.  
* Evaluate the Asker's question: Read the clarifying question just submitted by the Asker. Use the provided scales to rate how relevant and informative their question is.  
* Answer the question: Write a direct and accurate response to the Asker's clarifying question based on your hidden knowledge. Provide only the specific information they asked for. Do not volunteer extra hints or solve the puzzle for them.