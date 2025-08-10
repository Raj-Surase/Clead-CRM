import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Send, CheckCircle, AlertCircle, Search, X } from "lucide-react";
import { toast } from "@/hooks/use-toast";
import { crmApi } from "@/lib/crmAPI";
import { Lead, Platform, Template, Campaign, leadApi, authApi } from "@/lib/api";
import { Input } from "@/components/ui/input";

export default function SendMessage() {
  const [messageForm, setMessageForm] = useState({
    lead_ids: [],
    platform_id: "",
    template_id: "",
    campaign_id: "",
    message_content: ""
  });
  const [validationResults, setValidationResults] = useState<any>(null);
  const [platforms, setPlatforms] = useState<Platform[]>([]);
  const [templates, setTemplates] = useState<Template[]>([]);
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [leads, setLeads] = useState<Lead[]>([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [filteredLeads, setFilteredLeads] = useState<Lead[]>([]);
  const [showLeadResults, setShowLeadResults] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      const userId = await authApi.getUserId();
    // Fetch platforms
    crmApi.getPlatforms(userId).then(setPlatforms);
    // Fetch templates
    crmApi.getOutreachTemplates(userId).then(setTemplates);
    // Fetch campaigns
    crmApi.getCampaigns(userId).then(res => setCampaigns(res.campaigns || res));
    }
    fetchData();
  }, []);

  useEffect(() => {
    // Fetch all leads on mount
    leadApi.getLeads().then(res => {
      const leadsData = Array.isArray(res) ? res : res.leads;
      setLeads(leadsData || []);
    });
  }, []);

  useEffect(() => {
    // Filter leads based on search term
    if (searchTerm.trim() === '') {
      setFilteredLeads([]);
      setShowLeadResults(false);
      return;
    }
    const searchTermLower = searchTerm.toLowerCase();
    const filtered = leads.filter(lead => {
      return (
        lead.full_name?.toLowerCase().includes(searchTermLower) ||
        lead.email?.toLowerCase().includes(searchTermLower) ||
        lead.company?.toLowerCase().includes(searchTermLower) ||
        lead.phone?.toLowerCase().includes(searchTermLower) ||
        lead.job_title?.toLowerCase().includes(searchTermLower) ||
        lead.city?.toLowerCase().includes(searchTermLower) ||
        lead.country?.toLowerCase().includes(searchTermLower)
      );
    });
    setFilteredLeads(filtered);
    setShowLeadResults(true);
  }, [searchTerm, leads]);

  const handleLeadSelect = (lead: Lead) => {
    setMessageForm(prev => ({
      ...prev,
      lead_ids: prev.lead_ids.includes(lead.id) ? prev.lead_ids : [...prev.lead_ids, lead.id]
    }));
    setSearchTerm("");
    setShowLeadResults(false);
  };

  const handleRemoveLead = (leadId: number) => {
    setMessageForm(prev => ({
      ...prev,
      lead_ids: prev.lead_ids.filter(id => id !== leadId)
    }));
  };

  const handleTemplateSelect = (templateId: string) => {
    const template = templates.find((t: any) => t.id.toString() === templateId);
    if (template) {
      setMessageForm(prev => ({
        ...prev,
        template_id: templateId,
        message_content: template.content
      }));
    }
  };

  const handleSendMessage = async () => {
    if (!messageForm.message_content || !messageForm.platform_id || !messageForm.lead_ids.length) {
      toast({
        title: "Send Error",
        description: "Please fill in all required fields.",
        variant: "destructive"
      });
      return;
    }
    try {
      const userId = await authApi.getUserId();
      await crmApi.sendMessage(userId, {
        lead_ids: messageForm.lead_ids,
        platform_id: Number(messageForm.platform_id),
        message_content: messageForm.message_content
      });
      toast({
        title: "Messages Sent",
        description: `Successfully sent messages to ${messageForm.lead_ids.length} leads`,
      });
      setMessageForm({
        lead_ids: [],
        platform_id: "",
        template_id: "",
        campaign_id: "",
        message_content: ""
      });
      setValidationResults(null);
    } catch (err) {
      toast({
        title: "Send Error",
        description: "Failed to send messages. Please try again.",
        variant: "destructive"
      });
    }
  };

  return (
    <div className="p-6  min-h-screen">
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold text-black">Send Message</h1>
          <p className="text-gray-600">Send messages to your leads across different platforms</p>
        </div>

        {/* Message Form */}
        <Card className="border border-black">
          <CardHeader>
            <CardTitle className="text-black">Compose Message</CardTitle>
            <CardDescription>Fill in the details to send your outreach message</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Lead Selection */}
            <div>
              <Label className="text-black">Select Leads *</Label>
              <div className="relative">
                <Input
                  type="text"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  placeholder="Search leads by name, email, company..."
                  className="border-black focus:ring-black pr-10"
                />
                {searchTerm && (
                  <button
                    type="button"
                    onClick={() => setSearchTerm("")}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700"
                  >
                    <X className="h-4 w-4" />
                  </button>
                )}
              </div>
              {showLeadResults && filteredLeads.length > 0 && (
                <div className="absolute z-50 mt-1 w-full  rounded-md shadow-lg border border-gray-200 max-h-60 overflow-auto">
                  <div className="p-2">
                    {filteredLeads.map((lead) => (
                      <button
                        key={lead.id}
                        type="button"
                        onClick={() => handleLeadSelect(lead)}
                        className="w-full text-left px-3 py-2 hover:bg-gray-100 rounded-md transition-colors flex flex-col"
                      >
                        <span className="font-medium">{lead.full_name}</span>
                        <span className="text-sm text-gray-500">
                          {lead.company} • {lead.email}
                        </span>
                        <span className="text-xs text-gray-400">
                          {[
                            lead.job_title,
                            lead.phone,
                            `${lead.city}${lead.country ? `, ${lead.country}` : ''}`
                          ].filter(Boolean).join(' • ')}
                        </span>
                      </button>
                    ))}
                  </div>
                </div>
              )}
              {showLeadResults && filteredLeads.length === 0 && searchTerm && (
                <div className="absolute z-50 mt-1 w-full  rounded-md shadow-lg border border-gray-200">
                  <div className="p-4 text-center text-gray-500">
                    No leads found matching "{searchTerm}"
                  </div>
                </div>
              )}
              {messageForm.lead_ids.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-2">
                  {messageForm.lead_ids.map((leadId) => {
                    const lead = leads.find((l: any) => l.id === leadId);
                    return (
                      <Badge key={leadId} variant="outline" className="border-black flex items-center gap-1">
                        {lead?.full_name || leadId}
                        <button
                          type="button"
                          className="ml-1 text-gray-400 hover:text-red-500"
                          onClick={() => handleRemoveLead(leadId)}
                        >
                          <X className="h-3 w-3" />
                        </button>
                      </Badge>
                    );
                  })}
                </div>
              )}
            </div>

            {/* Platform Selection */}
            <div>
              <Label className="text-black">Platform *</Label>
              <Select 
                value={messageForm.platform_id} 
                onValueChange={(value) => setMessageForm(prev => ({ ...prev, platform_id: value }))}
              >
                <SelectTrigger className="border-black">
                  <SelectValue placeholder="Select platform" />
                </SelectTrigger>
                <SelectContent className=" border-black">
                  {platforms.map((platform: any) => (
                    <SelectItem key={platform.id} value={platform.id.toString()}>
                      {platform.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Template Selection */}
            <div>
              <Label className="text-black">Template (Optional)</Label>
              <Select 
                value={messageForm.template_id} 
                onValueChange={handleTemplateSelect}
              >
                <SelectTrigger className="border-black">
                  <SelectValue placeholder="Select template" />
                </SelectTrigger>
                <SelectContent className=" border-black">
                  {templates.map((template: any) => (
                    <SelectItem key={template.id} value={template.id.toString()}>
                      {template.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Campaign Selection */}
            <div>
              <Label className="text-black">Campaign (Optional)</Label>
              <Select 
                value={messageForm.campaign_id} 
                onValueChange={(value) => setMessageForm(prev => ({ ...prev, campaign_id: value }))}
              >
                <SelectTrigger className="border-black">
                  <SelectValue placeholder="Associate with campaign" />
                </SelectTrigger>
                <SelectContent className=" border-black">
                  {campaigns.map((campaign: any) => (
                    <SelectItem key={campaign.id} value={campaign.id.toString()}>
                      {campaign.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Message Content */}
            <div>
              <Label className="text-black">Message Content *</Label>
              <Textarea
                value={messageForm.message_content}
                onChange={(e) => setMessageForm(prev => ({ ...prev, message_content: e.target.value }))}
                className="border-black min-h-32"
                placeholder="Enter your message content..."
              />
              <p className="text-xs text-gray-500 mt-1">
                Use {`{{name}}`} for personalization
              </p>
            </div>

            {/* Actions */}
            <div className="flex gap-3">
              <Button 
                onClick={handleSendMessage}
                className="bg-black text-white hover:bg-gray-800"
                disabled={!messageForm.message_content || !messageForm.platform_id || !messageForm.lead_ids.length}
              >
                <Send className="w-4 h-4 mr-2" />
                Send Messages
              </Button>
              <Button 
                variant="outline"
                onClick={() => {
                  setMessageForm({
                    lead_ids: [],
                    platform_id: "",
                    template_id: "",
                    campaign_id: "",
                    message_content: ""
                  });
                  setValidationResults(null);
                }}
                className="border-black text-black hover:bg-gray-100"
              >
                Clear
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
