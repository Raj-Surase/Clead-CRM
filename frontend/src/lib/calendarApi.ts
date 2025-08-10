import { getHeaders, handleApiError } from './authUtils';
import {
  Attendee,
  AvailabilityResponse,
  CalendarSummaryResponse,
  Event,
  EventConflictsResponse,
  NextAvailableSlot,
  Campaign,
  HealthCheckResponse,
  PaginatedEventsResponse,
  EventStatsResponse,
  LeadEventSummaryResponse,
  FollowUpSuggestion,
  SuggestedMeetingTimesResponse,
  Lead
} from './api';
import { authApi } from './api';

class CalendarApi {
  private baseUrl = 'http://127.0.0.1:8000/calendar';
  private outreachBaseUrl = 'http://127.0.0.1:8000/outreach/api/v1';
  private userIdPromise: Promise<string> | null = null;
  private userId: string | null = null;

  private async getUserId(): Promise<string> {
    if (this.userId) return this.userId;
    if (!this.userIdPromise) {
      this.userIdPromise = authApi.getUserId().then(id => {
        this.userId = id;
        return id;
      });
    }
    return this.userIdPromise;
  }

  private async request<T>(endpoint: string, options: RequestInit = {}, useOutreachBase: boolean = false): Promise<T> {
    const baseUrl = useOutreachBase ? this.outreachBaseUrl : this.baseUrl;
    return handleApiError(async () => {
      const response = await fetch(`${baseUrl}${endpoint}`, {
        ...options,
        headers: { ...getHeaders(), ...options.headers },
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'API request failed');
      }

      if (response.status === 204) {
        return {} as T;
      }

      return response.json();
    });
  }

  // Event Management
  async createEvent(data: any) {
    const userId = await this.getUserId();
    return this.request<Event>('/api/events', {
      method: 'POST',
      body: JSON.stringify({ ...data, user_id: userId }),
    });
  }

  async getEvents(params: any = {}) {
    const userId = await this.getUserId();
    const queryParams = new URLSearchParams(
      Object.entries(params)
        .filter(([_, value]) => value !== undefined)
        .map(([key, value]) => [key, String(value)])
    ).toString();
    return this.request<PaginatedEventsResponse>(`/api/users/${userId}/events?${queryParams}`);
  }

  async getUpcomingEvents(params: { limit?: number } = {}) {
    const userId = await this.getUserId();
    const queryParams = new URLSearchParams(
      Object.entries(params)
        .filter(([_, value]) => value !== undefined)
        .map(([key, value]) => [key, String(value)])
    ).toString();
    return this.request<Event[]>(`/api/users/${userId}/events/upcoming?${queryParams}`);
  }

  async getEventStats(params: { start_date?: string; end_date?: string } = {}) {
    const userId = await this.getUserId();
    const queryParams = new URLSearchParams(
      Object.entries(params)
        .filter(([_, value]) => value !== undefined)
        .map(([key, value]) => [key, String(value)])
    ).toString();
    return this.request<EventStatsResponse>(`/api/users/${userId}/events/stats?${queryParams}`);
  }

  async getEventById(
    eventId: number,
    params: {
      include_attendees?: boolean;
      include_lead_info?: boolean;
    } = {}
  ) {
    const userId = await this.getUserId();
    const queryParams = new URLSearchParams(
      Object.entries(params)
        .filter(([_, value]) => value !== undefined)
        .map(([key, value]) => [key, String(value)])
    ).toString();
    return this.request<Event>(`/api/users/${userId}/events/${eventId}?${queryParams}`);
  }

  async updateEvent(
    eventId: number,
    data: any
  ) {
    const userId = await this.getUserId();
    return this.request<Event>(`/api/events/${eventId}`, {
      method: 'PUT',
      body: JSON.stringify({ ...data, user_id: userId }),
    });
  }

  async deleteEvent(eventId: number) {
    const userId = await this.getUserId();
    return this.request<void>(`/api/users/${userId}/events/${eventId}`, {
      method: 'DELETE',
    });
  }

  // Attendee Management
  async addAttendeeToEvent(
    eventId: number,
    data: any
  ) {
    const userId = await this.getUserId();
    return this.request<Attendee>(`/api/events/${eventId}/attendees`, {
      method: 'POST',
      body: JSON.stringify({ ...data, user_id: userId }),
    });
  }

  async getEventAttendees(
    eventId: number,
    params: { include_lead_info?: boolean } = {}
  ) {
    const userId = await this.getUserId();
    const queryParams = new URLSearchParams(
      Object.entries(params)
        .filter(([_, value]) => value !== undefined)
        .map(([key, value]) => [key, String(value)])
    ).toString();
    return this.request<Attendee[]>(`/api/users/${userId}/events/${eventId}/attendees?${queryParams}`);
  }

  async updateAttendee(
    attendeeId: number,
    data: any
  ) {
    const userId = await this.getUserId();
    return this.request<Attendee>(`/api/attendees/${attendeeId}`, {
      method: 'PUT',
      body: JSON.stringify({ ...data, user_id: userId }),
    });
  }

  async updateAttendeeResponse(
    attendeeId: number,
    data: any
  ) {
    const userId = await this.getUserId();
    return this.request<Attendee>(`/api/users/${userId}/attendees/${attendeeId}/response`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async deleteAttendee(attendeeId: number) {
    const userId = await this.getUserId();
    return this.request<void>(`/api/users/${userId}/attendees/${attendeeId}`, {
      method: 'DELETE',
    });
  }

  // Campaign Management
  async getCampaigns(params: any = {}) {
    const queryParams = new URLSearchParams(
      Object.entries(params)
        .filter(([_, value]) => value !== undefined)
        .map(([key, value]) => [key, String(value)])
    ).toString();
    return this.request<Campaign[]>(`/api/v1/campaigns?${queryParams}`, {}, true);
  }

  async addLeadsToCampaign(campaignId: number, leadIds: number[]) {
    return this.request<void>(`/api/v1/campaigns/${campaignId}/leads/bulk`, {
      method: 'POST',
      body: JSON.stringify(leadIds),
    }, true);
  }

  // Availability & Scheduling
  async checkAvailability(data: any) {
    const userId = await this.getUserId();
    return this.request<AvailabilityResponse>('/api/availability/check', {
      method: 'POST',
      body: JSON.stringify({ ...data, user_id: userId }),
    });
  }

  async findNextAvailableSlot(params: any) {
    const userId = await this.getUserId();
    const queryParams = new URLSearchParams(
      Object.entries(params)
        .filter(([_, value]) => value !== undefined)
        .map(([key, value]) => [key, String(value)])
    ).toString();
    return this.request<NextAvailableSlot>(`/api/users/${userId}/availability/next-slot?${queryParams}`);
  }

  async suggestMeetingTimes(params: any) {
    const userId = await this.getUserId();
    const queryParams = new URLSearchParams(
      Object.entries(params)
        .filter(([_, value]) => value !== undefined)
        .map(([key, value]) => [key, String(value)])
    ).toString();
    return this.request<SuggestedMeetingTimesResponse>(`/api/users/${userId}/availability/suggest-times?${queryParams}`);
  }

  // Calendar Summary
  async getCalendarSummary(params: any = {}) {
    const userId = await this.getUserId();
    const queryParams = new URLSearchParams(
      Object.entries(params)
        .filter(([_, value]) => value !== undefined && value !== '')
        .map(([key, value]) => [key, String(value)])
    ).toString();
    const url = queryParams ? `/api/users/${userId}/calendar/summary?${queryParams}` : `/api/users/${userId}/calendar/summary`;
    return this.request<CalendarSummaryResponse>(url);
  }

  // Lead Integration
  async createEventFromLead(
    leadId: number,
    data: any
  ) {
    const userId = await this.getUserId();
    return this.request<Event>(`/api/leads/${leadId}/events`, {
      method: 'POST',
      body: JSON.stringify({ ...data, user_id: userId }),
    });
  }

  async getLeadEvents(leadId: number) {
    const userId = await this.getUserId();
    return this.request<Event[]>(`/api/users/${userId}/leads/${leadId}/events`);
  }

  async getLeadEventSummary(leadId: number) {
    const userId = await this.getUserId();
    return this.request<LeadEventSummaryResponse>(`/api/users/${userId}/leads/${leadId}/events/summary`);
  }

  async getFollowUpSuggestions(leadId: number) {
    const userId = await this.getUserId();
    return this.request<FollowUpSuggestion[]>(`/api/users/${userId}/leads/${leadId}/follow-up-suggestions`);
  }

  async syncLeadUpdates(leadId: number) {
    const userId = await this.getUserId();
    return this.request<void>(`/api/leads/${leadId}/sync`, {
      method: 'PUT',
      body: JSON.stringify({ user_id: userId }),
    });
  }

  async getLeadsWithUpcomingEvents(params: { days_ahead?: number } = {}) {
    const userId = await this.getUserId();
    const queryParams = new URLSearchParams(
      Object.entries(params)
        .filter(([_, value]) => value !== undefined)
        .map(([key, value]) => [key, String(value)])
    ).toString();
    return this.request<{ leads: Lead[] }>(`/api/users/${userId}/leads/upcoming-events?${queryParams}`);
  }

  // Utility Endpoints
  async checkHealth() {
    return this.request<HealthCheckResponse>('/health');
  }

  async checkEventConflicts(eventId: number) {
    const userId = await this.getUserId();
    return this.request<EventConflictsResponse>(`/api/users/${userId}/events/${eventId}/conflicts`);
  }
}

export const calendarApi = () => new CalendarApi();