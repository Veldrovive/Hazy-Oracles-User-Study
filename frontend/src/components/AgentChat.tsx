import { Box, Typography } from '@mui/material';
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
import { useEffect } from 'react';

export interface AgentChatProps {
    imageSrc: string;
    imageSide: 'incoming' | 'outgoing';
    initialMessages: any[];
    onSend: (message: string) => void;
    firstResponseRef: React.RefObject<Element>;
    lastResponseRef: React.RefObject<Element>;
    loading: boolean;
}

export function AgentChat({ imageSrc, imageSide, initialMessages, onSend, firstResponseRef, lastResponseRef, loading }: AgentChatProps) {

    useEffect(() => {
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
        <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%', width: '100%', bgcolor: 'white' }}>
            <Box sx={{ flexGrow: 1, p: 0, display: 'flex', flexDirection: 'column', minHeight: 400 }}>
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
                                {initialMessages.slice(0, -1).map((msg, i) => (
                                    <Message key={msg.id || i} model={msg} id={`msg-${i}`} />
                                ))}
                                <Message
                                    model={initialMessages[initialMessages.length - 1]}
                                    id="last-message"
                                />
                                {
                                    loading &&
                                    <Message model={{ direction: "outgoing", position: "single" }}>
                                        <Message.CustomContent>
                                            <Loader />
                                        </Message.CustomContent>
                                    </Message>
                                }
                            </MessageList>
                            <MessageInput attachButton={false} placeholder="Type message here" onSend={onSend} disabled={loading} />
                        </ChatContainer>
                    </MainContainer>
                </div>
            </Box>
        </Box>
    );
}
