import { sendEmail } from './utils/ .js';

app.post('/api/send-email', async (req, res) => {
  const { to, subject, text, html } = req.body;

  if (!to || !subject || (!text && !html)) {
    return res.status(400).json({ error: 'Missing email parameters' });
  }

  try {
    const info = await sendEmail({ to, subject, text, html });
    res.json({ success: true, messageId: info.messageId });
  } catch (error) {
    res.status(500).json({ error: 'Failed to send email' });
  }
});
