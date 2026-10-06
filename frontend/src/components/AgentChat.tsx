import { Box, Button } from '@mui/material';
import "@chatscope/chat-ui-kit-styles/dist/default/styles.min.css";
import {
    MainContainer,
    ChatContainer,
    MessageList,
    Message,
    MessageInput,
    ConversationHeader,
    Loader
} from "@chatscope/chat-ui-kit-react";
import { useEffect, useState } from 'react';

export interface AgentChatProps {
    imageSrc: string;
    imageSide: 'incoming' | 'outgoing';
    initialMessages: any[];
    onSend: (message: string) => Promise<boolean> | boolean | void;
    firstResponseRef: React.RefObject<Element>;
    lastResponseRef: React.RefObject<Element>;
    loading: boolean;
    textPlaceholder: string;
    messageHtml?: string;
    onMessageChange?: (html: string, text: string) => void;
}

export function AgentChat({ imageSrc, imageSide, initialMessages, onSend, firstResponseRef, lastResponseRef, loading, textPlaceholder, messageHtml: _messageHtml, onMessageChange }: AgentChatProps) {
    const [msgInputValue, setMsgInputValue] = useState("");

    const handleSendClick = async (_innerHtml: string, textContent: string, _innerText: string) => {
        // If the API allows passing both, onSend can be awaited to see if it succeeded.
        const success = await onSend(textContent);
        if (success !== false) {
            setMsgInputValue("");
        }
    };

    useEffect(() => {
        console.log("ImageSrc", imageSrc);
        const lastMessageContainer = document.getElementById("last-message");
        if (lastMessageContainer) {
            lastResponseRef.current = lastMessageContainer.children[0];
        } else {
            console.log("Last message not found", lastResponseRef.current);
        }

        const firstMessageContainer = document.getElementById("msg-0");
        if (firstMessageContainer) {
            firstResponseRef.current = firstMessageContainer.children[0];
        } else {
            console.log("First message not found", firstResponseRef.current);
        }
    }, [imageSrc, initialMessages]);


    return (
        <Box sx={{ display: 'flex', flexDirection: 'column', flex: 1, minHeight: 0, width: '100%', bgcolor: 'white' }}>
            <Box id="chat-box" sx={{ flexGrow: 1, p: 0, display: 'flex', flexDirection: 'column', minHeight: 400 }}>
                <div style={{ position: "relative", height: "100%", flexGrow: 1 }}>
                    <MainContainer>
                        <ChatContainer>
                            <ConversationHeader>
                                <ConversationHeader.Content
                                    userName="Chat History"
                                />
                            </ConversationHeader>
                            <MessageList>
                                <Message model={{
                                    direction: imageSide,
                                    position: "single",
                                }}>
                                    <Message.ImageContent src={imageSrc} width="100%"></Message.ImageContent>
                                </Message>
                                {initialMessages.map((msg, i) => (
                                    <Message
                                        key={msg.id || i}
                                        model={msg}
                                        id={i === initialMessages.length - 1 && i !== 0 ? "last-message" : `msg-${i}`}
                                    >
                                        {msg.is_flagged && (
                                            <Message.CustomContent>
                                                <div style={{ color: 'black' }}>{msg.message}</div>
                                                <div style={{ border: '2px solid red', padding: '8px', marginTop: '4px', borderRadius: '4px', backgroundColor: '#ffebee' }}>
                                                    <div style={{ color: 'red', fontSize: '0.85em', fontWeight: 'bold' }}>
                                                        ⚠️ Flagged: {msg.flagged_reason}
                                                    </div>
                                                </div>
                                            </Message.CustomContent>
                                        )}
                                    </Message>
                                ))}
                                {
                                    loading &&
                                    <Message model={{ direction: "outgoing", position: "single" }}>
                                        <Message.CustomContent>
                                            <Loader />
                                        </Message.CustomContent>
                                    </Message>
                                }
                            </MessageList>
                            <MessageInput
                                autoFocus
                                id="chat-input"
                                attachButton={false}
                                placeholder={textPlaceholder}
                                value={msgInputValue}
                                onChange={(innerHtml, textContent, _innerText) => {
                                    setMsgInputValue(innerHtml);
                                    if (onMessageChange) {
                                        onMessageChange(innerHtml, textContent);
                                    }
                                }}
                                onSend={handleSendClick}
                                disabled={loading}
                                sendButton={false}
                            ></MessageInput>
                            <Button>Test</Button>
                        </ChatContainer>
                    </MainContainer>
                </div>
            </Box>
        </Box>
    );
}
