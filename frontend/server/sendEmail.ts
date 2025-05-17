import nodemailer from 'nodemailer';

export const sendEmail = async ({ to, subject, text, html }) => {
  try {
    const transporter = nodemailer.createTransport({
      host: process.env.SMTP_HOST,       // e.g., smtp.gmail.com
      port: parseInt(process.env.SMTP_PORT || '587'), // Usually 587
      secure: false,                      // Use `true` for port 465
      auth: {
        user: process.env.SMTP_USER,     // Your email address
        pass: process.env.SMTP_PASS      // Your email app password (not regular password)
      }
    });

    const mailOptions = {
      from: `"AI Support" <${process.env.SMTP_USER}>`,
      to,
      subject,
      text,
      html
    };

    const info = await transporter.sendMail(mailOptions);
    return info;
  } catch (error) {
    console.error('Error sending email:', error);
    throw error;
  }
};
