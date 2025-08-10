import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Edit, UserPlus, Users, Trash2, BarChart3, Plus, User, Mail, Phone, Building, MapPin, Globe, Star, ExternalLink } from "lucide-react";
import { toast } from "@/hooks/use-toast";
import { crmApi } from "@/lib/crmAPI";
import type { CampaignStatistics, CampaignLead, Template, Lead } from "@/lib/api";
import { leadApi } from "@/lib/leadApi";
import { Dialog as ConfirmDialog, DialogContent as ConfirmDialogContent, DialogHeader as ConfirmDialogHeader, DialogTitle as ConfirmDialogTitle, DialogDescription } from "@/components/ui/dialog";
import { DialogFooter } from "@/components/ui/dialog";
import { Loader2 } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { authApi } from "@/lib/authApi";
import { Skeleton } from "@/components/ui/skeleton";

export default function CampaignDetails() {
  const { campaignId } = useParams();
  const navigate = useNavigate();
  const [statistics, setStatistics] = useState<CampaignStatistics | null>(null);
  const [leads, setLeads] = useState<CampaignLead[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [isAddLeadModalOpen, setIsAddLeadModalOpen] = useState(false);
  const [newLead, setNewLead] = useState({ lead_id: "", status: "active" });
  const [addLeadLoading, setAddLeadLoading] = useState(false);
  const [addLeadError, setAddLeadError] = useState<string | null>(null);
  const [editCampaignForm, setEditCampaignForm] = useState({
    name: '',
    status: '',
    description: ''
  });
  const [editCampaignLoading, setEditCampaignLoading] = useState(false);
  const [editCampaignError, setEditCampaignError] = useState<string | null>(null);
  const [leadsList, setLeadsList] = useState<Lead[]>([]);
  const [leadSearchTerm, setLeadSearchTerm] = useState("");
  const [filteredLeads, setFilteredLeads] = useState<Lead[]>([]);
  const [showLeadResults, setShowLeadResults] = useState(false);
  const [selectedLead, setSelectedLead] = useState<Lead | null>(null);
  const [deleteLeadId, setDeleteLeadId] = useState<number | null>(null);
  const [deleteLoading, setDeleteLoading] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);
  const [viewLeadDialogOpen, setViewLeadDialogOpen] = useState(false);
  const [viewLead, setViewLead] = useState<Lead | null>(null);
  // Send Email Dialog State
  const [isSendDialogOpen, setIsSendDialogOpen] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [platforms, setPlatforms] = useState([]);
  const [templates, setTemplates] = useState<Template[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState<string>("");

  const [sendForm, setSendForm] = useState({
    platform_id: "1",
    message_content: "",
    subject: "",
    template_id: "",
    user_id: 1,
  });

  const getStatusColor = (status: string) => {
    switch (status) {
      case "new": return "bg-blue-50 text-blue-700 border-blue-200";
      case "contacted": return "bg-green-50 text-green-700 border-green-200";
      case "qualified": return "bg-purple-50 text-purple-700 border-purple-200";
      case "converted": return "bg-emerald-50 text-emerald-700 border-emerald-200";
      default: return "bg-gray-50 text-gray-700 border-gray-200";
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case "high": return "bg-red-50 text-red-700 border-red-200";
      case "medium": return "bg-yellow-50 text-yellow-700 border-yellow-200";
      case "low": return "bg-gray-50 text-gray-700 border-gray-200";
      case "urgent": return "bg-red-100 text-red-800 border-red-300";
      default: return "bg-gray-50 text-gray-700 border-gray-200";
    }
  };

  useEffect(() => {
    const fetchData = async () => {
      if (!campaignId) return;
      setIsLoading(true);
      setError(null);
      try {
        const userId = await authApi.getUserId(); 
        const [stats, leadsRes] = await Promise.all([
          crmApi.getCampaignStatistics(userId, Number(campaignId)),
          crmApi.getCampaignLeads(userId, Number(campaignId)),
        ]);
        setStatistics(stats as CampaignStatistics);
        setLeads(leadsRes as CampaignLead[]);
        // Set edit form defaults from fetched campaign
        if (stats && stats.campaign) {
          setEditCampaignForm({
            name: stats.campaign.name || '',
            status: stats.campaign.status || '',
            description: stats.campaign.description || ''
          });
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch campaign data');
      } finally {
        setIsLoading(false);
      }
    };
    fetchData();
  }, [campaignId]);

  // Fetch leads when Add Lead dialog opens
  useEffect(() => {
    if (isAddLeadModalOpen && leadsList.length === 0) {
      (async () => {
        try {
          const response = await leadApi.getLeads();
          setLeadsList(response.leads);
        } catch (error) {
          setAddLeadError("Failed to fetch leads");
        }
      })();
    }
    if (!isAddLeadModalOpen) {
      setLeadSearchTerm("");
      setFilteredLeads([]);
      setShowLeadResults(false);
      setSelectedLead(null);
      setNewLead({ lead_id: "", status: "active" });
    }
  }, [isAddLeadModalOpen]);

  // Filter leads as user types
  useEffect(() => {
    if (leadSearchTerm.trim() === "") {
      setFilteredLeads([]);
      setShowLeadResults(false);
      return;
    }
    const searchTermLower = leadSearchTerm.toLowerCase();
    const filtered = leadsList.filter(lead =>
      lead.full_name?.toLowerCase().includes(searchTermLower) ||
      lead.email?.toLowerCase().includes(searchTermLower) ||
      lead.company?.toLowerCase().includes(searchTermLower) ||
      lead.phone?.toLowerCase().includes(searchTermLower) ||
      lead.job_title?.toLowerCase().includes(searchTermLower) ||
      lead.city?.toLowerCase().includes(searchTermLower) ||
      lead.country?.toLowerCase().includes(searchTermLower)
    );
    setFilteredLeads(filtered);
    setShowLeadResults(true);
  }, [leadSearchTerm, leadsList]);

  // Fetch platforms for send email dialog
  useEffect(() => {
    if (!isSendDialogOpen) return;
    const fetchPlatforms = async () => {
      try {
        const userId = await authApi.getUserId();
        const response = await crmApi.getPlatforms(userId);
        setPlatforms(response);
      } catch (error) {
        toast({ title: "Failed to fetch platforms", description: "Unable to load communication platforms. Please try again." });
      }
    };
    fetchPlatforms();
    // Fetch templates
    const fetchTemplates = async () => {
      try {
        const userId = await authApi.getUserId();
        const response = await crmApi.getOutreachTemplates(userId);
        setTemplates(response || []);
      } catch (error) {
        toast({ title: "Failed to fetch templates", description: "Unable to load templates. Please try again." });
      }
    };
    fetchTemplates();
  }, [isSendDialogOpen]);

  // When template is selected, fill message_content and subject
  useEffect(() => {
    if (!selectedTemplate || selectedTemplate === "none") return;
    const template = templates.find(t => t.id.toString() === selectedTemplate);
    if (template) {
      setSendForm(f => ({
        ...f,
        message_content: template.content,
        subject: template.subject || "", // Set subject from template if available
        template_id: template.id.toString()
      }));
    }
  }, [selectedTemplate, templates]);

  const handleUpdateCampaign = async () => {
    if (!campaignId) return;
    setEditCampaignLoading(true);
    setEditCampaignError(null);
    try {
      const body = {
        name: editCampaignForm.name,
        status: editCampaignForm.status,
        description: editCampaignForm.description
      };
      const userId = await authApi.getUserId();
      const updated = await crmApi.updateCampaign(userId, Number(campaignId), body);
      setStatistics(prev => prev ? ({
        ...prev,
        campaign: {
          ...prev.campaign,
          ...updated
        }
      }) : prev);
      setIsEditModalOpen(false);
      toast({
        title: "Campaign Updated",
        description: "Campaign details have been updated successfully.",
      });
    } catch (err) {
      setEditCampaignError(err instanceof Error ? err.message : "Failed to update campaign. Please try again.");
    } finally {
      setEditCampaignLoading(false);
    }
  };

  const handleAddLead = async () => {
    if (!campaignId || !newLead.lead_id) return;
    setAddLeadLoading(true);
    setAddLeadError(null);
    try {
      const body = {
        lead_id: Number(newLead.lead_id),
        status: newLead.status,
        user_id: 1,
      };
      const userId = await authApi.getUserId();
      const response = await crmApi.addLeadsToCampaign(userId, Number(campaignId), body);
      const addedLead = Array.isArray(response) ? response[0] : response;
  
      // Find the lead in leadsList to get the name
      const leadDetails = leadsList.find(l => l.id === Number(newLead.lead_id));
      const lead_name = leadDetails ? leadDetails.full_name : '';
  
      // Add the name to the new lead object
      setLeads(prev => [
        ...prev,
        {
          ...addedLead,
          lead_name, // Ensure name is set
        }
      ]);
      setNewLead({ lead_id: "", status: "active" });
      setIsAddLeadModalOpen(false);
      toast({
        title: "Lead Added",
        description: "Lead has been added to the campaign successfully.",
      });
    } catch (err) {
      setAddLeadError(err instanceof Error ? err.message : "Failed to add lead. Please try again.");
    } finally {
      setAddLeadLoading(false);
    }
  };

  const handleLeadSelect = (lead: Lead) => {
    setSelectedLead(lead);
    setNewLead(prev => ({ ...prev, lead_id: lead.id.toString() }));
    setLeadSearchTerm(lead.full_name);
    setShowLeadResults(false);
  };

  const handleDeleteLead = async () => {
    if (!campaignId || deleteLeadId == null) return;
    setDeleteLoading(true);
    setDeleteError(null);
    try {
      const userId = await authApi.getUserId();
      await crmApi.removeLeadFromCampaign(userId, Number(campaignId), deleteLeadId);
      setLeads(prev => prev.filter(l => l.lead_id !== deleteLeadId));
      setDeleteLeadId(null);
      toast({
        title: "Lead Removed",
        description: "Lead has been removed from the campaign.",
      });
    } catch (err) {
      setDeleteError(err instanceof Error ? err.message : "Failed to remove lead. Please try again.");
    } finally {
      setDeleteLoading(false);
    }
  };

  const handleViewLead = async (leadId: number) => {
    try {
      const lead = await leadApi.getLead(leadId);
      setViewLead(lead);
      setViewLeadDialogOpen(true);
    } catch (err) {
      toast({
        title: "Failed to fetch lead",
        description: err instanceof Error ? err.message : "Unable to load lead details.",
      });
    }
  };

  const handleSendEmail = async () => {
    if (!sendForm.message_content.trim()) {
      toast({ title: "Message content is required" });
      return;
    }
    setIsSending(true);
    try {
      const body = {
        lead_ids: [],
        platform_id: parseInt(sendForm.platform_id),
        message_content: sendForm.message_content,
        subject: sendForm.subject || "", // Always send a string, never null
        template_id: sendForm.template_id ? parseInt(sendForm.template_id) : null,
        campaign_id: Number(campaignId),
        user_id: sendForm.user_id,
      };
      const userId = await authApi.getUserId();
      const response = await crmApi.sendMessage(userId, body);
      toast({
        title: "Email(s) sent",
        description: `Success: ${response.success_count || 0}, Failed: ${response.failed_count || 0}`,
      });
      setIsSendDialogOpen(false);
      setSendForm({ platform_id: "1", message_content: "", subject: "", template_id: "", user_id: 1 }); // Reset subject
    } catch (error) {
      toast({
        title: "Failed to send email(s)",
        description: error instanceof Error ? error.message : "An error occurred. Please try again.",
      });
    } finally {
      setIsSending(false);
    }
  };

  if (isLoading) {
    return (
      <div className="p-6 min-h-screen">
        <div className="max-w-7xl mx-auto space-y-6">
          <div className="flex justify-between items-center">
            <div>
              <Skeleton className="h-10 w-64 mb-2" />
              <Skeleton className="h-4 w-40" />
            </div>
            <div className="flex gap-3">
              <Skeleton className="h-10 w-32" />
              <Skeleton className="h-10 w-32" />
              <Skeleton className="h-10 w-32" />
            </div>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {[...Array(4)].map((_, i) => (
              <Skeleton key={i} className="h-24 w-full" />
            ))}
          </div>
          <Skeleton className="h-40 w-full mt-6" />
          <Skeleton className="h-40 w-full mt-6" />
          <Skeleton className="h-96 w-full mt-6" />
        </div>
      </div>
    );
  }
  if (error) {
    return <div className="p-6 min-h-screen text-red-500">{error}</div>;
  }
  if (!statistics) {
    return <div className="p-6 min-h-screen">No campaign data found.</div>;
  }
  const { campaign } = statistics;

  return (
    <div className="p-6 min-h-screen">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-black">{campaign.name}</h1>
            <p className="text-gray-600">Campaign Details</p>
          </div>
          <div className="flex gap-3">
            <Dialog open={isEditModalOpen} onOpenChange={setIsEditModalOpen}>
              <DialogTrigger asChild>
                <Button variant="outline" className="text-black hover:bg-gray-100">
                  <Edit className="w-4 h-4 mr-2" />
                  Edit Campaign
                </Button>
              </DialogTrigger>
              <DialogContent className="">
                <DialogHeader>
                  <DialogTitle className="text-black">Edit Campaign</DialogTitle>
                </DialogHeader>
                <div className="space-y-4">
                  <div>
                    <Label htmlFor="edit-name" className="text-black">Name</Label>
                    <Input
                      id="edit-name"
                      value={editCampaignForm.name}
                      onChange={e => setEditCampaignForm(f => ({ ...f, name: e.target.value }))}
                      className=""
                    />
                  </div>
                  <div>
                    <Label htmlFor="edit-status" className="text-black">Status</Label>
                    <Select
                      value={editCampaignForm.status}
                      onValueChange={value => setEditCampaignForm(f => ({ ...f, status: value }))}
                    >
                      <SelectTrigger className="">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent className="">
                        <SelectItem value="active">Active</SelectItem>
                        <SelectItem value="paused">Paused</SelectItem>
                        <SelectItem value="closed">Closed</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label htmlFor="edit-description" className="text-black">Description</Label>
                    <Input
                      id="edit-description"
                      value={editCampaignForm.description}
                      onChange={e => setEditCampaignForm(f => ({ ...f, description: e.target.value }))}
                      className=""
                    />
                  </div>
                  {editCampaignError && <div className="text-red-500 text-sm">{editCampaignError}</div>}
                  <div className="flex gap-2">
                    <Button onClick={handleUpdateCampaign} className="bg-black text-white hover:bg-gray-800" disabled={editCampaignLoading}>
                      {editCampaignLoading ? 'Updating...' : 'Update Campaign'}
                    </Button>
                    <Button variant="outline" onClick={() => setIsEditModalOpen(false)} className="text-black hover:bg-gray-100" disabled={editCampaignLoading}>
                      Cancel
                    </Button>
                  </div>
                </div>
              </DialogContent>
            </Dialog>
            <Dialog open={isAddLeadModalOpen} onOpenChange={setIsAddLeadModalOpen}>
              <DialogTrigger asChild>
                <Button className="bg-black text-white hover:bg-gray-800">
                  <UserPlus className="w-4 h-4 mr-2" />
                  Add Lead
                </Button>
              </DialogTrigger>
              <DialogContent className="">
                <DialogHeader>
                  <DialogTitle className="text-black">Add Lead to Campaign</DialogTitle>
                </DialogHeader>
                <div className="space-y-4">
                  <div className="relative">
                    <Label htmlFor="lead-search" className="text-black">Search Lead</Label>
                    <Input
                      id="lead-search"
                      type="text"
                      value={leadSearchTerm}
                      onChange={e => {
                        setLeadSearchTerm(e.target.value);
                        setSelectedLead(null);
                        setNewLead(prev => ({ ...prev, lead_id: "" }));
                      }}
                      placeholder="Search leads by name, email, company..."
                      className="focus:ring-black pr-10"
                    />
                    {leadSearchTerm && (
                      <button
                        type="button"
                        onClick={() => {
                          setLeadSearchTerm("");
                          setSelectedLead(null);
                          setNewLead(prev => ({ ...prev, lead_id: "" }));
                        }}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700"
                      >
                        ×
                      </button>
                    )}
                    {showLeadResults && filteredLeads.length > 0 && (
                      <div className="absolute z-50 mt-1 w-full rounded-md shadow-lg border border-gray-200 max-h-60 overflow-auto">
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
                    {showLeadResults && filteredLeads.length === 0 && leadSearchTerm && (
                      <div className="absolute z-50 mt-1 w-full rounded-md shadow-lg border border-gray-200">
                        <div className="p-4 text-center text-gray-500">
                          No leads found matching "{leadSearchTerm}"
                        </div>
                      </div>
                    )}
                    {selectedLead && (
                      <div className="mt-2 p-2 bg-gray-50 rounded-md">
                        <div className="text-sm">
                          <span className="font-medium">Selected Lead: </span>
                          {selectedLead.full_name}
                        </div>
                        <div className="text-xs text-gray-500">
                          {selectedLead.company} • {selectedLead.email} • {selectedLead.phone}
                        </div>
                      </div>
                    )}
                  </div>
                  <div>
                    <Label htmlFor="lead-status" className="text-black">Status</Label>
                    <Select value={newLead.status} onValueChange={(value) => setNewLead(prev => ({ ...prev, status: value }))}>
                      <SelectTrigger className="">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent className="">
                        <SelectItem value="active">Active</SelectItem>
                        <SelectItem value="inactive">Inactive</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  {addLeadError && <div className="text-red-500 text-sm">{addLeadError}</div>}
                  <div className="flex gap-2">
                    <Button 
                      onClick={handleAddLead}
                      className="bg-black text-white hover:bg-gray-800"
                      disabled={!selectedLead || addLeadLoading}
                    >
                      {addLeadLoading ? 'Adding...' : 'Add Lead'}
                    </Button>
                    <Button variant="outline" onClick={() => setIsAddLeadModalOpen(false)} className="text-black hover:bg-gray-100" disabled={addLeadLoading}>
                      Cancel
                    </Button>
                  </div>
                </div>
              </DialogContent>
            </Dialog>
            <Dialog open={isSendDialogOpen} onOpenChange={setIsSendDialogOpen}>
              <DialogTrigger asChild>
                <Button className="bg-black text-white hover:bg-gray-800">
                  <Plus className="w-4 h-4 mr-2" />
                  Send Emails
                </Button>
              </DialogTrigger>
              <DialogContent className="sm:max-w-[500px]">
                <DialogHeader>
                  <DialogTitle>Send Email to Campaign</DialogTitle>
                  <DialogDescription>
                    Send an email to all leads in this campaign.
                  </DialogDescription>
                </DialogHeader>
                <div className="grid gap-4 py-4">
                  <div>
                    <label className="text-sm font-medium mb-1 block">Platform *</label>
                    <Select
                      value={sendForm.platform_id}
                      onValueChange={(value) => setSendForm((f) => ({ ...f, platform_id: value }))}
                    >
                      <SelectTrigger className="">
                        <SelectValue placeholder="Select platform" />
                      </SelectTrigger>
                      <SelectContent>
                        {platforms.map((platform) => (
                          <SelectItem key={platform.id} value={platform.id.toString()}>
                            {platform.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <label className="text-sm font-medium mb-1 block">Template</label>
                    <Select
                      value={selectedTemplate}
                      onValueChange={setSelectedTemplate}
                    >
                      <SelectTrigger className="">
                        <SelectValue placeholder="Select template (optional)" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="none">None</SelectItem>
                        {templates.map((template) => (
                          <SelectItem key={template.id} value={template.id.toString()}>
                            {template.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <label className="text-sm font-medium mb-1 block">Subject</label>
                    <Input
                      type="text"
                      value={sendForm.subject}
                      onChange={(e) => setSendForm((f) => ({ ...f, subject: e.target.value }))}
                      placeholder="Enter subject (optional for email)"
                      className="focus:ring-black"
                    />
                  </div>
                  <div>
                    <label className="text-sm font-medium mb-1 block">Message Content *</label>
                    <Input
                      type="text"
                      value={sendForm.message_content}
                      onChange={(e) => setSendForm((f) => ({ ...f, message_content: e.target.value }))}
                      placeholder="Enter your message"
                      className="focus:ring-black"
                    />
                  </div>
                  <div>
                    <label className="text-sm font-medium mb-1 block">Campaign</label>
                    <Input
                      type="text"
                      value={campaign.name}
                      disabled
                      className="bg-gray-100 text-gray-500"
                    />
                  </div>
                </div>
                <DialogFooter>
                  <Button
                    type="submit"
                    onClick={handleSendEmail}
                    className="bg-black text-white hover:bg-gray-800"
                    disabled={isSending}
                  >
                    {isSending ? (
                      <>
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        Sending...
                      </>
                    ) : (
                      'Send Email'
                    )}
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </div>
        </div>
        {/* Campaign Details Card */}
        <Card className="border">
          <CardHeader>
            <CardTitle className="text-black">Campaign Information</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid md:grid-cols-2 gap-6">
              <div className="space-y-3">
                <div>
                  <h4 className="font-semibold text-black">Description</h4>
                  <p className="text-gray-700">{campaign.description}</p>
                </div>
                <div>
                  <h4 className="font-semibold text-black">Status</h4>
                  <span className={`px-2 py-1 rounded text-xs ${
                    campaign.status === 'active' 
                      ? 'bg-green-100 text-green-800' 
                      : 'bg-gray-100 text-gray-800'
                  }`}>
                    {campaign.status}
                  </span>
                </div>
              </div>
              <div className="space-y-3">
                <div>
                  <h4 className="font-semibold text-black">Start Date</h4>
                  <p className="text-gray-700">{campaign.start_date}</p>
                </div>
                <div>
                  <h4 className="font-semibold text-black">End Date</h4>
                  <p className="text-gray-700">{campaign.end_date || "No end date"}</p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
        {/* Statistics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <Card className="border">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-black">Total Leads</CardTitle>
              <Users className="h-4 w-4 text-black" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-black">{statistics.total_leads}</div>
            </CardContent>
          </Card>
          <Card className="border">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-black">Messages Sent</CardTitle>
              <BarChart3 className="h-4 w-4 text-black" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-black">{statistics.total_messages_sent}</div>
            </CardContent>
          </Card>
          <Card className="border">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-black">Avg Messages/Lead</CardTitle>
              <BarChart3 className="h-4 h-4 text-black" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-black">{statistics.average_messages_per_lead.toFixed(2)}</div>
            </CardContent>
          </Card>
          <Card className="border">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-black">Lead Status</CardTitle>
              <BarChart3 className="h-4 w-4 text-black" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-black">
                {Object.entries(statistics.lead_status_breakdown).map(([status, count]) => (
                  <span key={status}>{count} </span>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
        {/* Leads Table */}
        <Card className="border">
          <CardHeader>
            <CardTitle className="text-black">Campaign Leads ({leads.length})</CardTitle>
            <CardDescription>Leads associated with this campaign</CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="text-black">Lead Name</TableHead>
                  <TableHead className="text-black">Status</TableHead>
                  <TableHead className="text-black">Added Date</TableHead>
                  <TableHead className="text-black">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {leads.map((lead: CampaignLead) => (
                  <TableRow 
                    key={lead.id} 
                    className="hover:bg-gray-50 cursor-pointer"
                    onClick={() => handleViewLead(lead.lead_id)}
                  >
                    <TableCell className="text-black font-medium">{lead.lead_name}</TableCell>
                    <TableCell>
                      <span className={`px-2 py-1 rounded text-xs ${
                        lead.status === 'active' 
                          ? 'bg-green-100 text-green-800' 
                          : 'bg-gray-100 text-gray-800'
                      }`}>
                        {lead.status}
                      </span>
                    </TableCell>
                    <TableCell className="text-black">{lead.added_at}</TableCell>
                    <TableCell onClick={e => e.stopPropagation()}>
                      <div className="flex gap-2">
                        <Button 
                          size="sm" 
                          variant="outline" 
                          className="border-red-500 text-red-500 hover:bg-red-50"
                          onClick={() => setDeleteLeadId(lead.lead_id)}
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
        {/* View Lead Dialog */}
        <Dialog open={viewLeadDialogOpen} onOpenChange={setViewLeadDialogOpen}>
          <DialogContent className="w-3/4 max-w-7xl h-[75vh] overflow-y-auto">
            {viewLead && (
              <div className="space-y-6">
                <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4">
                  <div className="flex-1">
                    <h1 className="text-2xl lg:text-3xl font-bold text-black">{viewLead.full_name}</h1>
                    <p className="text-gray-600 mt-1">{viewLead.job_title} at {viewLead.company}</p>
                  </div>
                </div>
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                  <div className="lg:col-span-2">
                    <Card className="">
                      <CardHeader>
                        <CardTitle className="text-black flex items-center">
                          <User className="w-5 h-5 mr-2" />
                          Lead Information
                        </CardTitle>
                        <CardDescription>Contact details and professional information</CardDescription>
                      </CardHeader>
                      <CardContent className="space-y-6">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <div className="space-y-4">
                            <div className="flex items-start gap-3">
                              <Mail className="w-5 h-5 text-gray-600 mt-0.5" />
                              <div>
                                <p className="text-sm text-gray-600">Email</p>
                                <a href={`mailto:${viewLead.email}`} className="font-medium text-black hover:text-blue-600">{viewLead.email}</a>
                                
                                <Badge className="ml-2 bg-green-50 text-green-700 border-green-200">Valid</Badge>
                                
                              </div>
                            </div>
                            <div className="flex items-start gap-3">
                              <Phone className="w-5 h-5 text-gray-600 mt-0.5" />
                              <div>
                                <p className="text-sm text-gray-600">Phone</p>
                                <a href={`tel:${viewLead.phone}`} className="font-medium text-black hover:text-blue-600">{viewLead.phone}</a>
                                
                                <Badge className="ml-2 bg-green-50 text-green-700 border-green-200">Valid</Badge>
                                
                              </div>
                            </div>
                            <div className="flex items-start gap-3">
                              <Building className="w-5 h-5 text-gray-600 mt-0.5" />
                              <div>
                                <p className="text-sm text-gray-600">Company & Role</p>
                                <p className="font-medium text-black">{viewLead.company}</p>
                                <p className="text-sm text-gray-600">{viewLead.job_title}</p>
                              </div>
                            </div>
                          </div>
                          <div className="space-y-4">
                            <div className="flex items-start gap-3">
                              <MapPin className="w-5 h-5 text-gray-600 mt-0.5" />
                              <div>
                                <p className="text-sm text-gray-600">Location</p>
                                <p className="font-medium text-black">{viewLead.city}, {viewLead.country}</p>
                                <p className="text-sm text-gray-600">{viewLead.industry}</p>
                              </div>
                            </div>
                            <div className="flex items-start gap-3">
                              <Globe className="w-5 h-5 text-gray-600 mt-0.5" />
                              <div>
                                <p className="text-sm text-gray-600">LinkedIn</p>
                                <a href={viewLead.linkedin_url} target="_blank" rel="noopener noreferrer" className="font-medium text-black hover:text-blue-600 flex items-center">
                                  View Profile
                                  <ExternalLink className="w-3 h-3 ml-1" />
                                </a>
                              </div>
                            </div>
                            {/* <div className="flex items-start gap-3">
                              <Star className="w-5 h-5 text-gray-600 mt-0.5" />
                              <div>
                                <p className="text-sm text-gray-600">Lead Score</p>
                                <div className="flex items-center gap-2">
                                  <span className="text-2xl font-bold text-black">{viewLead.lead_score}</span>
                                  <span className="text-sm text-gray-600">/ 100</span>
                                </div>
                              </div>
                            </div> */}
                          </div>
                        </div>
                        <Separator className="bg-gray-200" />
                        <div>
                          <p className="text-sm text-gray-600 mb-3">Tags</p>
                          <div className="flex flex-wrap gap-2">
                            {viewLead.tags && viewLead.tags.split(',').map((tag: string, index: number) => (
                              <Badge key={index} className="bg-gray-100 text-gray-700 border-gray-300">{tag.trim()}</Badge>
                            ))}
                          </div>
                        </div>
                        {/* <div>
                          <p className="text-sm text-gray-600 mb-2">Data Completeness</p>
                          <div className="p-3 bg-gray-50 border border-gray-200 rounded-lg">
                            <div className="flex items-center justify-between mb-2">
                              <span className="text-black">Score:</span>
                              <span className="font-medium text-black">{viewLead.data_completeness_score}%</span>
                            </div>
                            <div className="flex items-center justify-between">
                              <span className="text-black">Social Profiles:</span>
                              <span className="font-medium text-black">{viewLead.social_profiles_count}</span>
                            </div>
                          </div>
                        </div> */}
                      </CardContent>
                    </Card>
                  </div>
                  <div className="space-y-6">
                    <Card className="">
                      <CardHeader>
                        <CardTitle className="text-black text-lg">Status & Priority</CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-4">
                        {/* <div>
                          <p className="text-sm text-gray-600 mb-2">Status</p>
                          <Badge className={getStatusColor(viewLead.lead_status)}>
                            {viewLead.lead_status.charAt(0).toUpperCase() + viewLead.lead_status.slice(1)}
                          </Badge>
                        </div>
                        <div>
                          <p className="text-sm text-gray-600 mb-2">Priority</p>
                          <Badge className={getPriorityColor(viewLead.priority)}>
                            {viewLead.priority.charAt(0).toUpperCase() + viewLead.priority.slice(1)}
                          </Badge>
                        </div> */}
                        <Separator className="bg-gray-200" />
                        <div>
                          <p className="text-sm text-gray-600 mb-1">Created</p>
                          <p className="text-black font-medium">{new Date(viewLead.created_at).toLocaleDateString()}</p>
                        </div>
                      </CardContent>
                    </Card>
                    <Card className="">
                      <CardHeader>
                        <CardTitle className="text-black text-lg">Source Information</CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-4">
                        <div>
                          <p className="text-sm text-gray-600 mb-1">Source File</p>
                          <p className="text-black font-medium">{viewLead.source_file_name}</p>
                          <p className="text-sm text-gray-600">Row {viewLead.source_file_row}</p>
                        </div>
                        <Separator className="bg-gray-200" />
                        <div>
                          <p className="text-sm text-gray-600 mb-1">Last Updated</p>
                          <p className="text-black font-medium">{new Date(viewLead.updated_at).toLocaleDateString()}</p>
                        </div>
                      </CardContent>
                    </Card>
                  </div>
                </div>
              </div>
            )}
          </DialogContent>
        </Dialog>
        {/* Confirm Delete Dialog */}
        <ConfirmDialog open={deleteLeadId !== null} onOpenChange={open => { if (!open) setDeleteLeadId(null); }}>
          <ConfirmDialogContent className="">
            <ConfirmDialogHeader>
              <ConfirmDialogTitle className="text-black">Confirm Lead Removal</ConfirmDialogTitle>
            </ConfirmDialogHeader>
            <div className="py-4 text-black">Are you sure you want to remove this lead from the campaign?</div>
            {deleteError && <div className="text-red-500 text-sm mb-2">{deleteError}</div>}
            <div className="flex gap-2 justify-end">
              <Button variant="outline" onClick={() => setDeleteLeadId(null)} className="text-black hover:bg-gray-100" disabled={deleteLoading}>
                Cancel
              </Button>
              <Button onClick={handleDeleteLead} className="bg-red-600 text-white hover:bg-red-700" disabled={deleteLoading}>
                {deleteLoading ? 'Removing...' : 'Remove'}
              </Button>
            </div>
          </ConfirmDialogContent>
        </ConfirmDialog>
      </div>
    </div>
  );
}