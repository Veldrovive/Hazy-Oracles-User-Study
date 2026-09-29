import type { Tour } from 'nextstepjs';

export const steps: Tour[] = [
  {
    tour: "asker-tour",
    steps: [
      {
        title: "Review Dialog History",
        content: "First, you should review the dialog history to understand the context of the current conversation.",
        selector: "#chat-box",
        side: 'left',
        showControls: true
      },
      {
        title: "Rate Previous Answer",
        content: "This box appears if there is a previous response. Think about how helpful you think this previous response is in reducing the ambiguity of the situation.",
        selector: "#rating-box",
        side: 'right',
        showControls: true
      },
      {
        title: "Answer the Original Question",
        content: "You have two main tasks: continuing the conversation, and trying to use the conversation to understand what the answer to the original question is. Do both every time no matter how ambiguous the situation currently is. In order to quantify how much ambiguity is left in the current conversation we also ask you to rate your confidence in your answer.",
        selector: "#current-guess-box",
        side: 'top',
        showControls: true
      },
      {
        title: "Formulate Next Question",
        content: "This is like texting with the other person. They answer the questions you ask. Your job is to formulate a question that you think will reduce ambiguity when answered. Even if you are very confident in your answer you should do your best to figure out a clarifying question that will be useful in pinpointing whether you are correct.",
        selector: "#chat-input",
        side: 'top',
        showControls: true
      },
      {
        title: "Submit Everything",
        content: "When you press the submit button, it will submit everything at once: your previous response score, your answer to the original question, and your next clarifying question.",
        selector: "#submit-button",
        side: 'top',
        showControls: true
      },
      {
        title: "Instructions",
        content: "You can reference this for a reminder of what you are doing.",
        selector: "#task-instructions",
        side: 'right',
        showControls: true
      },
      {
        title: "Detailed Instructions",
        content: "For detailed instructions you can press this 'i' icon.",
        selector: "#detailed-instructions-button",
        side: 'bottom',
        showControls: true
      }
    ]
  },
  {
    tour: "answerer-tour",
    steps: [
      {
        title: "Review Dialog History",
        content: "Review the dialog history.",
        selector: "#chat-box",
        side: 'left',
        showControls: true
      },
      {
        title: "Intended Question",
        content: "As an answerer you get access to information that is hidden from the asker. This is an unambiguous version of the question that the other person was asked. You should keep it as secret as possible while giving an honest and meaninful answer to the clarifying question you were asked. Basically, you should pretend that you don't understand why there is ambiguity.",
        selector: "#intended-question",
        side: 'right',
        showControls: true
      },
      {
        title: "Rate Previous Question",
        content: "Think about how helpful you think this previous question is in resolving the ambiguity of the situation.",
        selector: "#rating-box",
        side: 'top',
        showControls: true
      },
      {
        title: "Answer the Question",
        content: "Now you use the hidden knowledge from the intended question to answer the question from the previous message.",
        selector: "#chat-input",
        side: 'top',
        showControls: true
      },
      {
        title: "Submit Everything",
        content: "When you press the submit button, it will submit everything at once.",
        selector: "#submit-button",
        side: 'top',
        showControls: true
      },
      {
        title: "Instructions",
        content: "You can reference this for a reminder of what you are doing.",
        selector: "#task-instructions",
        side: 'right',
        showControls: true
      },
      {
        title: "Detailed Instructions",
        content: "For detailed instructions you can press this 'i' icon.",
        selector: "#detailed-instructions-button",
        side: 'bottom',
        showControls: true
      }
    ]
  }
];
