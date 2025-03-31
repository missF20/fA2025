import { Platform } from "../types";

/**
 * Get the color associated with a specific platform
 * 
 * @param platform The platform to get color for (facebook, instagram, whatsapp, slack, email)
 * @param isDarkTheme Whether the app is in dark mode
 * @returns The CSS color code for the platform
 */
export const getPlatformColor = (platform: Platform | string, isDarkTheme: boolean = false): string => {
  switch (platform.toLowerCase()) {
    case 'facebook':
      return isDarkTheme ? '#1877F2' : '#1877F2'; // Facebook blue
    case 'instagram':
      return isDarkTheme ? '#E1306C' : '#C13584'; // Instagram pink
    case 'whatsapp':
      return isDarkTheme ? '#25D366' : '#25D366'; // WhatsApp green
    case 'slack':
      return isDarkTheme ? '#4A154B' : '#611f69'; // Slack purple
    case 'email':
      return isDarkTheme ? '#00B2FF' : '#0078D4'; // Email blue
    default:
      return isDarkTheme ? '#6c757d' : '#6c757d'; // Default gray
  }
};

/**
 * Get the icon name for a specific platform
 * 
 * @param platform The platform to get icon for
 * @returns The Lucide icon name for the platform
 */
export const getPlatformIcon = (platform: Platform | string): string => {
  switch (platform.toLowerCase()) {
    case 'facebook':
      return 'facebook';
    case 'instagram':
      return 'instagram';
    case 'whatsapp':
      return 'message-circle';
    case 'slack':
      return 'hash';
    case 'email':
      return 'mail';
    default:
      return 'message-square';
  }
};

/**
 * Get the display name for a platform
 * 
 * @param platform The platform to get display name for
 * @returns The display name
 */
export const getPlatformDisplayName = (platform: Platform | string): string => {
  switch (platform.toLowerCase()) {
    case 'facebook':
      return 'Facebook';
    case 'instagram':
      return 'Instagram';
    case 'whatsapp':
      return 'WhatsApp';
    case 'slack':
      return 'Slack';
    case 'email':
      return 'Email';
    default:
      return platform.charAt(0).toUpperCase() + platform.slice(1);
  }
};