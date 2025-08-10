export interface HealthCheckResponse {
  status: string;
  timestamp: string;
  version: string;
  database: { [key: string]: string };
  integrations: { [key: string]: string };
}

export interface LeadStatisticsOverview {
  total_leads: number;
  contact_info: {
    email_valid: number;
    phone_valid: number;
    email_percentage: number;
    phone_percentage: number;
  };
  social_profiles: {
    linkedin: number;
    facebook: number;
    instagram: number;
    linkedin_percentage: number;
  };
}

export interface LeadGroupResponse {
  groups: Record<string, number>;
  total_leads: number;
  group_type: string;
}

export interface LeadLocationGroupResponse {
  groups: {
    [country: string]: {
      [state: string]: {
        [city: string]: number;
      };
    };
  };
  total_leads: number;
  group_type: string;
}

export interface LeadPlatformGroupResponse {
  groups: {
    email_available: number;
    phone_available: number;
    linkedin_available: number;
    facebook_available: number;
    instagram_available: number;
    twitter_available: number;
    multiple_platforms: number;
    no_contact_info: number;
  };
  total_leads: number;
  group_type: string;
}

export interface LeadEngagementGroupResponse {
  groups: Record<string, number>;
  total_leads: number;
  group_type: string;
}

export interface LeadSearchResponse {
  search_term: string;
  search_fields: string[];
  leads: Lead[];
  count: number;
}

export interface LeadFilterOptions {
  industries: string[];
  statuses: string[];
  sources: string[];
  priorities: string[];
  countries: string[];
  group_by_options: string[];
}

export interface Lead {
  id: number;
  first_name: string | null;
  last_name: string | null;
  full_name: string | null;
  email: string | null;
  phone: string | null;
  mobile: string | null;
  company: string | null;
  job_title: string | null;
  industry: string | null;
  city: string | null;
  country: string | null;
  linkedin_url: string | null;
  facebook_url: string | null;
  instagram_url: string | null;
  twitter_url: string | null;
  youtube_url: string | null;
  tiktok_url: string | null;
  website: string | null;
  created_at: string;
  updated_at: string;
  tags: string | null;
  source_file_name: string | null;
  source_file_row: number | null;
  user_id: string;
}

export interface LeadsResponse {
  leads: Lead[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

export interface FileUploadResponse {
  success: boolean;
  file_upload_id: number;
  stats: {
    created_leads: number;
    failed_leads: number;
    cleaning_warnings: string[];
  };
  created_leads: number[];
  failed_leads: string[];
}

export interface FileDeleteResponse {
  message: string;
  file_id: number;
  deleted_leads_count: number;
}

export interface FileHistoryEntry {
  id: number;
  filename: string;
  original_filename: string;
  file_type: string;
  file_size: number;
  mime_type: string | null;
  created_at: string;
  updated_at: string;
  user_id: string;
}

export interface Attendee {
  id?: number;
  event_id?: number;
  name: string;
  email: string;
  phone?: string;
  company?: string;
  job_title?: string;
  lead_id?: number;
  is_organizer: boolean;
  is_required: boolean;
  status?: string;
  response_datetime?: string;
  response_notes?: string;
  created_at?: string;
  updated_at?: string;
  lead_info?: Lead | null;
  user_id: string;
}

export interface Event {
  id?: number;
  title: string;
  description?: string;
  start_datetime: string;
  end_datetime: string;
  timezone: string;
  all_day: boolean;
  event_type: string;
  status: string;
  priority: string;
  location?: string;
  meeting_url?: string;
  meeting_id?: string | null;
  meeting_password?: string | null;
  lead_id?: number;
  lead_name?: string;
  lead_email?: string;
  lead_phone?: string;
  lead_company?: string;
  deal_value?: number;
  deal_stage?: string;
  deal_probability?: number | null;
  recurrence_type?: string;
  recurrence_interval?: number;
  recurrence_end_date?: string | null;
  recurrence_count?: number | null;
  parent_event_id?: number | null;
  notes?: string;
  tags?: string;
  custom_fields?: any | null;
  reminder_minutes?: number[];
  email_reminders?: boolean;
  sms_reminders?: boolean;
  duration_minutes?: number;
  is_recurring?: boolean;
  is_past?: boolean;
  is_upcoming?: boolean;
  is_active?: boolean;
  created_at?: string;
  updated_at?: string;
  attendees?: Attendee[];
  attendee_count?: number | null;
  lead_info?: Lead | null;
  user_id: string;
}

export interface PaginatedEventsResponse {
  events: Event[];
  pagination: {
    page: number;
    per_page: number;
    total: number;
    total_pages: number;
    has_next: boolean;
    has_prev: boolean;
  };
  user_id: string;
}

export interface EventStatsResponse {
  total_events: number;
  events_by_type: { [key: string]: number };
  events_by_status: { [key: string]: number };
  events_by_priority: { [key: string]: number };
  total_duration_minutes: number;
  average_duration_minutes: number;
}

export interface CalendarSummaryEvent {
  id: number;
  title: string;
  date: string;
  start_time: string;
  duration: number;
  type: string;
  status: string;
  lead_id?: number;
  lead_name?: string;
  priority: string;
  location?: string;
}

export interface CalendarSummaryResponse {
  start_date?: string;
  end_date?: string;
  total_events: number;
  total_duration_minutes: number;
  average_duration_minutes: number;
  events_by_day: {
    [date: string]: CalendarSummaryEvent[];
  };
  busiest_day: string | null;
  busiest_day_event_count: number;
}

export interface AvailabilitySlot {
  start_datetime: string;
  end_datetime: string;
  is_available: boolean;
  conflicting_event_id?: number;
  conflicting_event_title?: string;
}

export interface AvailabilityResponse {
  start_date: string;
  end_date: string;
  timezone: string;
  duration_minutes: number;
  buffer_minutes: number;
  slots_by_day: {
    [key: string]: Array<{
      start_datetime: string;
      end_datetime: string;
      is_available: boolean;
      conflicting_event_id: number | null;
      conflicting_event_title: string | null;
    }>;
  };
  total_slots: number;
  available_count: number;
  busy_count: number;
}

export interface NextAvailableSlot {
  start_datetime: string;
  end_datetime: string;
  duration_minutes: number;
  timezone: string;
}

export interface SuggestedMeetingTime {
  start_datetime: string;
  end_datetime: string;
  score: number;
  reason: string;
}

export interface SuggestedMeetingTimesResponse {
  duration_minutes: number;
  timezone: string;
  days_ahead: number;
  suggestions_by_day: {
    [date: string]: SuggestedMeetingTime[];
  };
  total_suggestions: number;
}

export interface EventConflict {
  id: number;
  title: string;
  start_datetime: string;
  end_datetime: string;
  event_type: string;
  status: string;
}

export interface EventConflictsResponse {
  event_id: number;
  has_conflicts: boolean;
  conflict_count: number;
  conflicts: EventConflict[];
}

export interface LeadEventSummaryResponse {
  lead_id: number;
  total_events: number;
  upcoming_events: number;
  completed_events: number;
  cancelled_events: number;
  total_duration_minutes: number;
  last_event_date?: string;
  next_event_date?: string;
}

export interface FollowUpSuggestion {
  suggestion_type: string;
  priority: string;
  description: string;
  recommended_time: string;
  event_type: string;
}

export interface Platform {
  id: number;
  name: string;
  description: string;
  user_id: string;
  created_at: string;
  updated_at: string;
}

export interface Template {
  id: number;
  name: string;
  subject: string | null;
  content: string;
  user_id: string;
  created_at: string;
  updated_at: string;
}

export interface Conversation {
  id: number;
  lead_id: number;
  platform_id: number;
  subject: string | null;
  status: string;
  last_message_at: string | null;
  created_at: string;
  updated_at: string;
  platform: Platform;
  user_id: string;
}

export interface OutreachMessage {
  id: number;
  lead_id: number;
  platform_id: number;
  message_content: string;
  campaign_id: number | null;
  bulk_group_id?: number | null;
  subject: string | null;
  user_id: string;
  sent_at: string;
  status: string;
  platform_message_id: string | null;
  error_message: string | null;
  created_at: string;
  updated_at: string;
  platform: Platform;
  bulk_message_group?: BulkMessageGroup | null;
}

export interface BulkMessageGroup {
  id: number;
  user_id: string;
  platform_id: number;
  campaign_id: number | null;
  total_leads: number;
  success_count: number;
  failed_count: number;
  subject: string | null;
  is_resend: boolean;
  parent_group_id: number | null;
  created_at: string;
  updated_at: string;
  platform: Platform;
  campaign?: Campaign | null;
}

export interface ConversationSummary {
  conversation: Conversation;
  total_messages: number;
  outgoing_messages: number;
  incoming_messages: number;
  first_message_at: string;
  last_message_at: string;
  response_rate: number;
}

export interface LeadConversations {
  lead_id: number;
  conversations?: Conversation[];
  count: number;
}

export interface ConversationSearch {
  search_term: string;
  conversations: Conversation[];
  count: number;
}

export interface IntegrationHealth {
  outreach_db: string;
  lead_parser_db: string;
  calendar_db: string;
  integration_status: string;
}

export interface IntegrationStatistics {
  total_leads: number;
  total_events: number;
  total_messages: number;
  total_conversations: number;
  leads_with_events: number;
  leads_with_messages: number;
  integration_coverage: {
    leads_with_events_percentage: number;
    leads_with_messages_percentage: number;
  };
}

export interface LeadEngagementScore {
  lead_id: number;
  engagement_score: number;
  engagement_level: string;
  factors: string[];
  metrics: {
    total_messages: number;
    total_conversations: number;
    active_conversations: number;
    completed_events: number;
    upcoming_events: number;
  };
}

export interface PlatformCredential {
  id: number;
  user_id: string;
  platform_id: number;
  username: string;
  created_at: string;
  updated_at: string;
}

export interface PlatformConnection {
  platform: Platform;
  credential: PlatformCredential | null;
  is_connected: boolean;
  username: string | null;
  connected_at: string | null;
}

export interface PlatformAuthResponse {
  success: boolean;
  message: string;
  credential_id: number;
}

export interface SendMessageResponse {
  success_count: number;
  failed_count: number;
  messages: OutreachMessage[];
  errors: string[];
}

export interface CampaignLead {
  lead_id: number;
  id: number;
  added_at: string;
  status: string;
  lead_name: string;
}

export interface Campaign {
  description: string;
  name: string;
  end_date: string;
  user_id: string;
  updated_at: string;
  start_date: string;
  id: number;
  status: string;
  created_at: string;
  total_leads: number;
}

export interface CampaignStatistics {
  campaign_id: number;
  campaign: Campaign;
  total_leads: number;
  lead_status_breakdown: {
    [status: string]: number;
  };
  total_messages_sent: number;
  average_messages_per_lead: number;
}

export interface ConversationDetails {
  lead_id: number;
  platform_id: number;
  subject: string | null;
  id: number;
  last_message_at: string | null;
  status: string;
  created_at: string;
  updated_at: string;
  platform: Platform;
  user_id: string;
}

import { fileApi } from './fileApi';
import { leadApi } from './leadApi';
import { crmApi } from './crmAPI';
import { calendarApi } from './calendarApi';
import { authApi } from './authApi';

export { fileApi, leadApi, crmApi, calendarApi, authApi };