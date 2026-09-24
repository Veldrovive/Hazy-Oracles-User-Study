import { Box, Typography, IconButton, Modal } from '@mui/material';
import InfoIcon from '@mui/icons-material/Info';
import { useBoolean } from 'usehooks-ts';

interface TaskInstructionsProps {
    instructions: string[];
    modalTitle?: string;
    modalContent?: React.ReactNode;
}

const style = {
    position: 'absolute',
    top: '50%',
    left: '50%',
    transform: 'translate(-50%, -50%)',
    width: '60%',
    bgcolor: 'background.paper',
    boxShadow: 24,
    borderRadius: 1,
    p: 4,
};

export function TaskInstructions({ instructions, modalTitle, modalContent }: TaskInstructionsProps) {
    const { value: instructionModalOpen, setTrue: handleOpenModal, setFalse: handleCloseModal } = useBoolean(false);
    return (
        <Box
            sx={{
                p: 2,
                mb: 2,
                bgcolor: '#e3f2fd', // light blue background
                borderRadius: 1,
                border: '1px solid #90caf9',
            }}
        >
            <Typography variant="h6" gutterBottom>
                Task Instructions
                <IconButton onClick={handleOpenModal} size="small" sx={{ ml: 1, color: 'action.active' }}>
                    <InfoIcon fontSize="small" />
                </IconButton>
            </Typography>

            <Modal
                open={instructionModalOpen}
                onClose={handleCloseModal}
                aria-labelledby="modal-modal-title"
                aria-describedby="modal-modal-description"
            >
                <Box sx={style}>
                    <Typography id="modal-modal-title" variant="h6" component="h2">
                        {modalTitle || "Task Instructions"}
                    </Typography>
                    <Typography id="modal-modal-description" sx={{ mt: 2 }}>
                        {modalContent || "Task Instructions"}
                    </Typography>
                </Box>
            </Modal>

            <ol style={{ margin: 0, paddingLeft: '1.5rem' }}>
                {instructions.map((instruction, index) => (
                    <li key={index}>
                        <Typography variant="body1">{instruction}</Typography>
                    </li>
                ))}
            </ol>
        </Box>
    );
}
