    # handle key press events for navigation
    def keyPressEvent(self, event: QKeyEvent):
        if self.fileName:
            # Left arrow - Reject (Toss) current image
            if event.key() == Qt.Key_Left:
                self.onTossDataClicked()
            
            # Right arrow - Accept current image and move to next
            elif event.key() == Qt.Key_Right:
                self.onAddDataClicked()
            
            # Up arrow - Increase threshold
            elif event.key() == Qt.Key_Up:
                newValue = self.threshValue.value() + self.threshValue.singleStep()
                self.threshValue.setValue(newValue)
                # Update preview after threshold changes
                self.onPreviewClicked()
            
            # Down arrow - Decrease threshold
            elif event.key() == Qt.Key_Down:
                newValue = self.threshValue.value() - self.threshValue.singleStep()
                self.threshValue.setValue(newValue)
                # Update preview after threshold changes
                self.onPreviewClicked()
        
        # Pass unhandled events to parent class
        super().keyPressEvent(event)
