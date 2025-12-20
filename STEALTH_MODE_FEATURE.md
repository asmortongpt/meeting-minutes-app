# Stealth Mode Feature - Meeting Minutes Pro

## Current Status: NOT IMPLEMENTED ❌

The current Meeting Minutes Pro implementation does **NOT** have built-in stealth/privacy features to prevent detection by other meeting participants during screen sharing.

## Privacy Concerns

### What Gets Exposed During Screen Sharing:
1. **Browser Tab Title**: Shows "Meeting Minutes App" in browser tabs
2. **Window Title**: Visible in taskbar/dock when sharing full desktop
3. **Visual Interface**: The entire meeting UI is visible if the window is shared
4. **Notifications**: Pop-up notifications could reveal the app's presence

## Recommended Stealth Mode Features

### 1. **Disguised Window Title**
```typescript
// frontend/src/hooks/useStealthMode.ts
export const useStealthMode = (enabled: boolean) => {
  useEffect(() => {
    if (enabled) {
      document.title = 'Google Docs - Untitled Document';
      // Or other innocuous titles like:
      // - 'Email - Inbox'
      // - 'Slack - General'
      // - 'Calendar - Today'
    } else {
      document.title = 'Meeting Minutes Pro';
    }
  }, [enabled]);
};
```

### 2. **Minimalist/Disguised UI Mode**
- **Notebook Mode**: Make the interface look like a simple notepad/text editor
- **Spreadsheet Mode**: Display as a basic spreadsheet interface
- **Chat Mode**: Appear as a messaging application
- **Hide Branding**: Remove all logos, colors, and identifiable elements

### 3. **Boss Key / Panic Button**
```typescript
// Quick hide with keyboard shortcut (e.g., Ctrl+Shift+H)
useEffect(() => {
  const handlePanicKey = (e: KeyboardEvent) => {
    if (e.ctrlKey && e.shiftKey && e.key === 'H') {
      // Option 1: Hide window completely (minimize)
      // Option 2: Switch to innocent-looking screen
      setStealthMode(true);
    }
  };

  window.addEventListener('keydown', handlePanicKey);
  return () => window.removeEventListener('keydown', handlePanicKey);
}, []);
```

### 4. **Notification Suppression**
```typescript
// Disable all notifications in stealth mode
if (stealthModeEnabled) {
  // No desktop notifications
  // No sound alerts
  // No visual popups
}
```

### 5. **Second Monitor Support**
- Automatically detect multiple monitors
- Suggest using non-shared monitor
- Warn when screen sharing is detected

### 6. **Mobile App Privacy**
For React Native mobile apps:
- **Picture-in-Picture Mode**: Keep app running in small overlay window
- **Background Transcription**: Run transcription without visible UI
- **App Switcher Privacy**: Blur/hide content in iOS/Android app switcher

## Implementation Priority

### High Priority (Immediate Need):
✅ **Disguised Window Title** - Easy to implement, high impact
✅ **Boss Key/Panic Button** - Quick escape mechanism
✅ **Notification Suppression** - Prevent accidental exposure

### Medium Priority (Nice to Have):
- Minimalist UI themes
- Screen sharing detection
- Multi-monitor guidance

### Low Priority (Advanced):
- Full disguise modes (spreadsheet, notepad, etc.)
- Advanced background modes

## Ethical Considerations

### ⚠️ Important Notes:

1. **Transparency**: This feature should be used for **personal productivity** and **privacy**, not deception
2. **Professional Use**: Useful for:
   - Taking personal notes during meetings
   - Maintaining privacy on personal devices
   - Preventing accidental exposure of sensitive content
3. **Not for**: Circumventing recording policies or hiding unauthorized recording

## Legal Compliance

**Meeting Recording Laws Vary by Location:**

- **One-Party Consent States**: Only one participant needs to consent (you)
- **Two-Party/All-Party Consent States**: ALL participants must consent
- **International**: Many countries require explicit consent

**Recommendation**:
- Always check local laws
- Include consent notification in app
- Add "This meeting is being recorded" disclaimer option
- Provide clear recording indicators

## Quick Implementation

To add basic stealth mode now, you would need to:

```bash
# 1. Create stealth mode hook
touch frontend/src/hooks/useStealthMode.ts

# 2. Add to settings context
# Edit frontend/src/contexts/SettingsContext.tsx

# 3. Add keyboard shortcut handler
# Edit frontend/src/App.tsx

# 4. Update HTML title dynamically
# Edit frontend/index.html to use dynamic title
```

## Current Workarounds

Until stealth mode is implemented, users can:

1. **Use Second Monitor**: Keep app on non-shared screen
2. **Use Mobile Device**: Use iOS/Android app instead of desktop
3. **Use Split Screen**: Keep app in background window
4. **Rename Browser Tab Manually**: Browser extensions can rename tabs
5. **Use PWA in Separate Window**: Install as PWA for cleaner window management

## Conclusion

**Answer to Your Question**:
❌ **No, the current implementation CANNOT load discreetly** - it has a clear "Meeting Minutes App" title and visible UI that would be detected if you share your screen.

**To make it stealth, you would need to implement the features above.**

Would you like me to implement basic stealth mode features now?
