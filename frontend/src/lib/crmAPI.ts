import { getHeaders, handleApiError } from './authUtils';
import { authApi } from './authApi';
import { Platform, Template, SendMessageResponse, BulkMessageGroup, OutreachMessage, Campaign, CampaignLead, CampaignStatistics } from './api';

class CrmApi {
  private baseUrl = 'http://127.0.0.1:8000/outreach/api/v1';

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    return handleApiError(async () => {
      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        ...options,
        headers: { ...getHeaders(), ...options.headers },
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error?.message || 'API request failed');
      }

      return response.json();
    });
  }

  // Platforms
  async getPlatforms(userId: string): Promise<Platform[]> {
    return this.request(`/platforms/user/${userId}/platforms`);
  }

  async createPlatform(userId: string, data: Partial<Platform>): Promise<Platform> {
    return this.request(`/platforms/platforms`, { 
      method: 'POST', 
      body: JSON.stringify({ ...data, user_id: userId })
    });
  }

  async getPlatform(userId: string, platformId: number): Promise<Platform> {
    return this.request(`/platforms/user/${userId}/platforms/${platformId}`);
  }

  async updatePlatform(userId: string, platformId: number, data: Partial<Platform>): Promise<Platform> {
    return this.request(`/platforms/user/${userId}/platforms/${platformId}`, { 
      method: 'PUT', 
      body: JSON.stringify({ ...data, user_id: userId }) 
    });
  }

  async deletePlatform(userId: string, platformId: number): Promise<void> {
    return this.request(`/platforms/user/${userId}/platforms/${platformId}`, { method: 'DELETE' });
  }

  async authenticatePlatform(userId: string, data: { platform_id: number, username: string, password: string }): Promise<any> {
    return this.request(`/platforms/user/${userId}/authenticate`, { 
      method: 'POST', 
      body: JSON.stringify({ ...data, user_id: userId }) 
    });
  }

  async getUserConnectedPlatforms(userId: string): Promise<any> {
    return this.request(`/platforms/user/${userId}/connected`);
  }

  async getUserAvailablePlatforms(userId: string): Promise<any> {
    return this.request(`/platforms/user/${userId}/available`);
  }

  async disconnectPlatform(userId: string, platformId: number): Promise<void> {
    return this.request(`/platforms/user/${userId}/platform/${platformId}/disconnect`, { method: 'DELETE' });
  }

  async initializeDefaultPlatforms(userId: string): Promise<void> {
    return this.request(`/platforms/user/${userId}/initialize-defaults`, { 
      method: 'POST',
      body: JSON.stringify({ user_id: userId })
    });
  }

  // Outreach Statistics
  async getOutreachStatistics(userId: string, params: { platform_id?: number } = {}): Promise<any> {
    const queryParams = new URLSearchParams();
    if (params.platform_id) queryParams.append('platform_id', params.platform_id.toString());
    return this.request(`/outreach/user/${userId}/overall?${queryParams}`);
  }

  // Outreach
  async sendMessage(userId: string, data: { lead_ids: number[], platform_id: number, message_content: string, subject?: string, template_id?: number, campaign_id?: number }): Promise<SendMessageResponse> {
    return this.request(`/outreach/user/${userId}/send-message`, { 
      method: 'POST', 
      body: JSON.stringify({ ...data, user_id: userId }) 
    });
  }

  async getOutreachMessages(userId: string, params: { skip?: number, limit?: number, platform_id?: number, lead_id?: number, status?: string, search?: string, bulk_group_id?: number } = {}): Promise<any> {
    const queryParams = new URLSearchParams();
    if (params.skip !== undefined) queryParams.append('skip', params.skip.toString());
    if (params.limit !== undefined) queryParams.append('limit', params.limit.toString());
    if (params.platform_id !== undefined) queryParams.append('platform_id', params.platform_id.toString());
    if (params.lead_id !== undefined) queryParams.append('lead_id', params.lead_id.toString());
    if (params.status) queryParams.append('status', params.status);
    if (params.search) queryParams.append('search', params.search);
    if (params.bulk_group_id !== undefined) queryParams.append('bulk_group_id', params.bulk_group_id.toString());
    return this.request(`/outreach/user/${userId}/messages?${queryParams}`);
  }
  
  

  async getOutreachMessage(userId: string, messageId: number): Promise<OutreachMessage> {
    return this.request(`/outreach/user/${userId}/messages/${messageId}`);
  }

  async updateOutreachMessage(userId: string, messageId: number, data: any): Promise<OutreachMessage> {
    return this.request(`/outreach/user/${userId}/messages/${messageId}`, { 
      method: 'PUT', 
      body: JSON.stringify({ ...data, user_id: userId }) 
    });
  }

  async deleteOutreachMessage(userId: string, messageId: number): Promise<void> {
    return this.request(`/outreach/user/${userId}/messages/${messageId}`, { method: 'DELETE' });
  }
  

  async validateLeads(userId: string, data: { lead_ids: number[] }, platformId?: number): Promise<any> {
    const query = platformId ? `?platform_id=${platformId}` : '';
    return this.request(`/outreach/user/${userId}/validate-leads${query}`, { 
      method: 'POST', 
      body: JSON.stringify({ ...data, user_id: userId }) 
    });
  }

  async getInvalidLeads(userId: string, platformId: number): Promise<any> {
    return this.request(`/outreach/user/${userId}/invalid-leads/${platformId}`);
  }

  async getMessageStats(userId: string, params: { platform_id?: number, bulk_group_id?: number } = {}): Promise<any> {
    const queryParams = new URLSearchParams();
    if (params.platform_id !== undefined) queryParams.append('platform_id', params.platform_id.toString());
    if (params.bulk_group_id !== undefined) queryParams.append('bulk_group_id', params.bulk_group_id.toString());
    return this.request(`/outreach/user/${userId}/message-stats?${queryParams}`);
  }

  async getBulkMessageGroups(userId: string, params: { platform_id?: number, campaign_id?: number } = {}): Promise<BulkMessageGroup[]> {
    const queryParams = new URLSearchParams();
    if (params.platform_id !== undefined) queryParams.append('platform_id', params.platform_id.toString());
    if (params.campaign_id !== undefined) queryParams.append('campaign_id', params.campaign_id.toString());
    return this.request(`/outreach/user/${userId}/bulk-message-groups?${queryParams}`);
  }

  /**
   * Delete all messages associated with a bulk message group for a user.
   * Mirrors the FastAPI endpoint:
   *   DELETE /outreach/user/{user_id}/bulk-messages/{bulk_group_id}
   */
  async deleteBulkMessageGroup(userId: string, bulkGroupId: number): Promise<{ message: string }> {
    return this.request(`/outreach/user/${userId}/bulk-messages/${bulkGroupId}`, {
      method: 'DELETE'
    });
  }

  async resendFailedMessages(userId: string, bulkGroupId: number): Promise<SendMessageResponse> {
    return this.request(`/outreach/user/${userId}/resend-failed-messages/${bulkGroupId}`, { 
      method: 'POST',
      body: JSON.stringify({ user_id: userId })
    });
  }

  // Leads
  async getLeads(userId: String, params: Record<string, any> = {}): Promise<any> {
    const queryParams = new URLSearchParams(params).toString();
    return this.request(`/leads/user/${userId}/leads?${queryParams}`);
  }

  async getLead(userId: String, leadId: number): Promise<any> {
    return this.request(`/leads/user/${userId}/leads/${leadId}`);
  }

  async searchLeads(userId: String, params: Record<string, any> = {}): Promise<any> {
    const queryParams = new URLSearchParams(params).toString();
    return this.request(`/leads/user/${userId}/search/?${queryParams}`);
  }

  async groupLeads(userId: String, data: any): Promise<any> {
    return this.request(`/leads/user/${userId}/group`, { method: 'POST', body: JSON.stringify(data) });
  }

  async groupLeadsByIndustry(userId: String): Promise<any> {
    return this.request(`/leads/user/${userId}/group/industry`);
  }

  async groupLeadsByStatus(userId: String): Promise<any> {
    return this.request(`/leads/user/${userId}/group/status`);
  }

  async groupLeadsBySource(userId: String): Promise<any> {
    return this.request(`/leads/user/${userId}/group/source`);
  }

  async groupLeadsByLocation(userId: String): Promise<any> {
    return this.request(`/leads/user/${userId}/group/location`);
  }

  async groupLeadsByPlatform(userId: String): Promise<any> {
    return this.request(`/leads/user/${userId}/group/platform`);
  }

  async groupLeadsByEngagement(userId: String): Promise<any> {
    return this.request(`/leads/user/${userId}/group/engagement`);
  }

  async getLeadStatisticsOverview(userId: String): Promise<any> {
    return this.request(`/leads/user/${userId}/statistics-overview`);
  }

  async getLeadFilterOptions(userId: String): Promise<any> {
    return this.request(`/leads/user/${userId}/filters/options`);
  }

  async getLeadOutreachHistory(userId: String, leadId: number): Promise<any> {
    return this.request(`/leads/user/${userId}/leads/${leadId}/outreach-history`);
  }

  // Conversations
  async createConversation(data: any): Promise<any> {
    return this.request('/conversations', { method: 'POST', body: JSON.stringify(data) });
  }

  async getConversations(params: Record<string, any> = {}): Promise<any> {
    const queryParams = new URLSearchParams(params).toString();
    return this.request(`/conversations?${queryParams}`);
  }

  async getConversation(conversationId: number): Promise<any> {
    return this.request(`/conversations/${conversationId}`);
  }

  async updateConversation(conversationId: number, data: any): Promise<any> {
    return this.request(`/conversations/${conversationId}`, { method: 'PUT', body: JSON.stringify(data) });
  }

  async deleteConversation(conversationId: number): Promise<void> {
    return this.request(`/conversations/${conversationId}`, { method: 'DELETE' });
  }

  async getConversationMessages(conversationId: number, params: Record<string, any> = {}): Promise<any> {
    const queryParams = new URLSearchParams(params).toString();
    return this.request(`/conversations/${conversationId}/messages?${queryParams}`);
  }

  async createConversationMessage(conversationId: number, data: any): Promise<any> {
    return this.request(`/conversations/${conversationId}/messages`, { method: 'POST', body: JSON.stringify(data) });
  }

  async closeConversation(conversationId: number): Promise<void> {
    return this.request(`/conversations/${conversationId}/close`, { method: 'POST' });
  }

  async reopenConversation(conversationId: number): Promise<void> {
    return this.request(`/conversations/${conversationId}/reopen`, { method: 'POST' });
  }

  async getConversationSummary(conversationId: number): Promise<any> {
    return this.request(`/conversations/${conversationId}/summary`);
  }

  async getConversationsForLead(leadId: number): Promise<any> {
    return this.request(`/conversations/lead/${leadId}`);
  }

  async searchConversations(params: Record<string, any> = {}): Promise<any> {
    const queryParams = new URLSearchParams(params).toString();
    return this.request(`/conversations/search/?${queryParams}`);
  }

  async emailWebhook(data: any, signature?: string): Promise<any> {
    const headers: HeadersInit = signature ? { 'X-Signature': signature } : {};
    return this.request('/conversations/webhooks/email', { 
      method: 'POST', 
      body: JSON.stringify(data),
      headers
    });
  }

  // Campaigns
  async createCampaign(userId: string, data: any): Promise<any> {
    return this.request(`/campaigns/campaigns`, { 
      method: 'POST', 
      body: JSON.stringify({ ...data, user_id: userId }) 
    });
  }

  async getCampaigns(userId: string, params: Record<string, any> = {}): Promise<any> {
    const queryParams = new URLSearchParams(params).toString();
    return this.request(`/campaigns/user/${userId}/campaigns?${queryParams}`);
  }

  async getCampaign(userId: string, campaignId: number): Promise<any> {
    return this.request(`/campaigns/user/${userId}/campaigns/${campaignId}`);
  }

  async updateCampaign(userId: string, campaignId: number, data: any): Promise<any> {
    return this.request(`/campaigns/user/${userId}/campaigns/${campaignId}`, { 
      method: 'PUT', 
      body: JSON.stringify({ ...data, user_id: userId }) 
    });
  }

  async deleteCampaign(userId: string, campaignId: number): Promise<void> {
    return this.request(`/campaigns/user/${userId}/campaigns/${campaignId}`, { method: 'DELETE' });
  }

  async addLeadsToCampaign(userId: string, campaignId: number, data: any): Promise<any> {
    return this.request(`/campaigns/user/${userId}/campaigns/${campaignId}/leads`, { 
      method: 'POST', 
      body: JSON.stringify({ ...data, user_id: userId }) 
    });
  }

  async getCampaignLeads(userId: string, campaignId: number, params: Record<string, any> = {}): Promise<any> {
    const queryParams = new URLSearchParams(params).toString();
    return this.request(`/campaigns/user/${userId}/campaigns/${campaignId}/leads?${queryParams}`);
  }

  async updateCampaignLeadStatus(userId: string, campaignId: number, leadId: number, data: any): Promise<any> {
    return this.request(`/campaigns/user/${userId}/campaigns/${campaignId}/leads/${leadId}`, { 
      method: 'PUT', 
      body: JSON.stringify({ ...data, user_id: userId }) 
    });
  }

  async removeLeadFromCampaign(userId: string, campaignId: number, leadId: number): Promise<void> {
    return this.request(`/campaigns/user/${userId}/campaigns/${campaignId}/leads/${leadId}`, { method: 'DELETE' });
  }

  async addBulkLeadsToCampaign(userId: string, campaignId: number, data: any): Promise<any> {
    return this.request(`/campaigns/user/${userId}/campaigns/${campaignId}/leads/bulk`, { 
      method: 'POST', 
      body: JSON.stringify({ ...data, user_id: userId }) 
    });
  }

  async getCampaignStatistics(userId: string, campaignId: number): Promise<any> {
    return this.request(`/campaigns/user/${userId}/campaigns/${campaignId}/statistics`);
  }

  // Template
  
  async createOutreachTemplate(userId: string, data: Partial<Template>): Promise<Template> {
    return this.request(`/campaigns/templates`, { 
      method: 'POST', 
      body: JSON.stringify({ ...data, user_id: userId }) 
    });
  }

  async getOutreachTemplates(userId: string, params: Record<string, any> = {}): Promise<Template[]> {
    // const queryParams = new URLSearchParams(params).toString();
    return this.request(`/campaigns/user/${userId}/templates`);
  }

  async getOutreachTemplate(userId: string, templateId: number): Promise<Template> {
    return this.request(`/campaigns/user/${userId}/templates/${templateId}`);
  }

  async updateOutreachTemplate(userId: string, templateId: number, data: Partial<Template>): Promise<Template> {
    return this.request(`/campaigns/user/${userId}/templates/${templateId}`, { 
      method: 'PUT', 
      body: JSON.stringify({ ...data, user_id: userId }) 
    });
  }

  async deleteOutreachTemplate(userId: string, templateId: number): Promise<void> {
    return this.request(`/campaigns/user/${userId}/templates/${templateId}`, { method: 'DELETE' });
  }

  // Integration
  async syncLeadContactStatus(userId: string, leadId: number, data: any, platformName?: string): Promise<any> {
    const query = platformName ? `?platform_name=${platformName}` : '';
    return this.request(`/integration/user/${userId}/sync-lead-contact-status/${leadId}${query}`, { 
      method: 'POST', 
      body: JSON.stringify({ ...data, user_id: userId }) 
    });
  }

  async createFollowUpEvent(userId: string, data: any, params: Record<string, any> = {}): Promise<any> {
    const queryParams = new URLSearchParams(params).toString();
    return this.request(`/integration/user/${userId}/create-follow-up-event?${queryParams}`, { 
      method: 'POST', 
      body: JSON.stringify({ ...data, user_id: userId }) 
    });
  }

  async getLeadsWithUpcomingEvents(userId: string, params: Record<string, any> = {}): Promise<any> {
    const queryParams = new URLSearchParams(params).toString();
    return this.request(`/integration/user/${userId}/leads-with-upcoming-events?${queryParams}`);
  }

  async getLeadsForOutreachBasedOnEvents(userId: string, params: Record<string, any> = {}): Promise<any> {
    const queryParams = new URLSearchParams(params).toString();
    return this.request(`/integration/user/${userId}/leads-for-outreach-based-on-events?${queryParams}`);
  }

  async syncConversationToCalendar(userId: string, conversationId: number, createFollowUp: boolean = false): Promise<any> {
    const query = createFollowUp ? '?create_follow_up=true' : '';
    return this.request(`/integration/user/${userId}/sync-conversation-to-calendar/${conversationId}${query}`, { 
      method: 'POST',
      body: JSON.stringify({ user_id: userId })
    });
  }

  async getLeadEngagementScore(userId: string, leadId: number): Promise<any> {
    return this.request(`/integration/user/${userId}/lead-engagement-score/${leadId}`);
  }

  async bulkSync(userId: string, data: any): Promise<any> {
    return this.request(`/integration/user/${userId}/bulk-sync`, { 
      method: 'POST', 
      body: JSON.stringify({ ...data, user_id: userId }) 
    });
  }

  async getIntegrationHealth(userId: string): Promise<any> {
    return this.request(`/integration/user/${userId}/integration-health`);
  }

  async getIntegrationStatistics(userId: string): Promise<any> {
    return this.request(`/integration/user/${userId}/integration-statistics`);
  }

  // Health
  async testApi(): Promise<any> {
    return this.request('/');
  }

  async checkApiHealth(): Promise<any> {
    return this.request('/health');
  }
}

export const crmApi = new CrmApi();