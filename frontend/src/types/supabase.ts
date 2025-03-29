export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[]

export interface Database {
  public: {
    Tables: {
      conversations: {
        Row: {
          id: string
          user_id: string
          platform: string
          client_name: string
          client_company: string
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: string
          user_id: string
          platform: string
          client_name: string
          client_company: string
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          user_id?: string
          platform?: string
          client_name?: string
          client_company?: string
          created_at?: string
          updated_at?: string
        }
      }
      interactions: {
        Row: {
          id: string
          platform: string
          client_name: string
          client_company: string
          user_id: string
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: string
          platform: string
          client_name: string
          client_company: string
          user_id: string
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          platform?: string
          client_name?: string
          client_company?: string
          user_id?: string
          created_at?: string
          updated_at?: string
        }
      }
      knowledge_files: {
        Row: {
          id: string
          user_id: string
          file_name: string
          file_size: number
          file_type: string
          content: any
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: string
          user_id?: string
          file_name: string
          file_size: number
          file_type: string
          content: any
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          user_id?: string
          file_name?: string
          file_size?: number
          file_type?: string
          content?: any
          created_at?: string
          updated_at?: string
        }
      }
      messages: {
        Row: {
          id: string
          conversation_id: string
          content: string
          sender_type: string
          created_at: string
        }
        Insert: {
          id?: string
          conversation_id: string
          content: string
          sender_type: string
          created_at?: string
        }
        Update: {
          id?: string
          conversation_id?: string
          content?: string
          sender_type?: string
          created_at?: string
        }
      }
      profiles: {
        Row: {
          id: string
          company: string | null
          created_at: string
          updated_at: string
          account_setup_complete: boolean
          welcome_email_sent: boolean
        }
        Insert: {
          id: string
          company?: string | null
          created_at?: string
          updated_at?: string
          account_setup_complete?: boolean
          welcome_email_sent?: boolean
        }
        Update: {
          id?: string
          company?: string | null
          created_at?: string
          updated_at?: string
          account_setup_complete?: boolean
          welcome_email_sent?: boolean
        }
      }
      responses: {
        Row: {
          id: string
          content: string
          platform: string
          user_id: string
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: string
          content: string
          platform: string
          user_id: string
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          content?: string
          platform?: string
          user_id?: string
          created_at?: string
          updated_at?: string
        }
      }
      tasks: {
        Row: {
          id: string
          description: string
          status: string
          platform: string
          client_name: string
          client_company: string
          user_id: string
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: string
          description: string
          status: string
          platform: string
          client_name: string
          client_company: string
          user_id: string
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          description?: string
          status?: string
          platform?: string
          client_name?: string
          client_company?: string
          user_id?: string
          created_at?: string
          updated_at?: string
        }
      }
    }
    Views: {
      [_ in never]: never
    }
    Functions: {
      get_first_user_id: {
        Args: Record<PropertyKey, never>
        Returns: string
      }
      handle_new_user: {
        Args: Record<PropertyKey, never>
        Returns: undefined
      }
    }
    Enums: {
      [_ in never]: never
    }
    CompositeTypes: {
      [_ in never]: never
    }
  }
}