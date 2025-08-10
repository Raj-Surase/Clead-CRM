import { useState, useEffect, useMemo } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Search, Loader2, Plus, X, ChevronLeft, ChevronRight, Eye, RefreshCw } from "lucide-react";
import { toast } from "sonner";
import { crmApi } from "@/lib/crmAPI";
import { leadApi } from "@/lib/leadApi";
import { Platform, Lead, Campaign, Template, OutreachMessage, BulkMessageGroup } from "@/lib/api";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter,
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { authApi } from "@/lib/authApi";
import { Skeleton } from "@/components/ui/skeleton";

interface GroupedMessage {
  id: string;
  bulk_group_id: number | null;
  platform_id: number;
  platform: Platform;
  message_content: string;
  subject: string | null;
  total_messages: number;
  sent_count: number;
  failed_count: number;
  delivered_count: number;
  read_count: number;
  sent_at: string;
  messages: OutreachMessage[];
}

export default function OutreachConversations() {
  const [bulkGroups, setBulkGroups] = useState<BulkMessageGroup[]>([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [perPage, setPerPage] = useState(10);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [selectedBulkGroup, setSelectedBulkGroup] = useState<BulkMessageGroup | null>(null);
  const [isBulkGroupDialogOpen, setIsBulkGroupDialogOpen] = useState(false);

  // Send Email Dialog State
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [leads, setLeads] = useState<Lead[]>([]);
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [platforms, setPlatforms] = useState<Platform[]>([]);
  const [leadSearchTerm, setLeadSearchTerm] = useState("");
  const [filteredLeads, setFilteredLeads] = useState<Lead[]>([]);
  const [selectedLeads, setSelectedLeads] = useState<Lead[]>([]);
  const [selectedCampaign, setSelectedCampaign] = useState("none");
  const [form, setForm] = useState({
    platform_id: "1",
    message_content: "",
    subject: "",
    template_id: "",
  });
  const [templates, setTemplates] = useState<Template[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState("none");

  // Add new state for dialog loading and fetched data
  const [dialogLoading, setDialogLoading] = useState(false);
  const [dialogBulkGroup, setDialogBulkGroup] = useState<BulkMessageGroup | null>(null);
  const [dialogMessages, setDialogMessages] = useState<OutreachMessage[]>([]);

  // Add state for editing and deleting messages
  const [editMessage, setEditMessage] = useState<OutreachMessage | null>(null);
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);
  const [editMessageContent, setEditMessageContent] = useState("");
  const [deleteMessageId, setDeleteMessageId] = useState<number | null>(null);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const [deleteBulkGroupId, setDeleteBulkGroupId] = useState<number | null>(null);
  const [isDeleteBulkGroupDialogOpen, setIsDeleteBulkGroupDialogOpen] = useState(false);

  // Only keep fetchBulkGroups for main table
  const fetchBulkGroups = async () => {
    try {
      const userId = await authApi.getUserId();
      const response = await crmApi.getBulkMessageGroups(userId, { });
      setBulkGroups(response || []);
    } catch (error) {
      toast("Failed to fetch bulk message groups", {
        description: "Unable to load bulk message groups. Please try again."
      });
    } finally {
      setIsLoading(false);
    }
  };

  // Only keep fetchBulkGroups for main table
  useEffect(() => {
    fetchBulkGroups();
  }, []);

  // Fetch platforms, leads, campaigns
  useEffect(() => {
    const fetchPlatforms = async () => {
      try {
        const userId = await authApi.getUserId();
        const response = await crmApi.getPlatforms(userId);
        setPlatforms(response);
      } catch (error) {
        toast("Failed to fetch platforms", {
          description: "Unable to load communication platforms. Please try again."
        });
      }
    };
    fetchPlatforms();

    const fetchLeads = async () => {
      try {
        const response = await leadApi.getLeads({ per_page: 100 });
        setLeads(response.leads);
      } catch (error) {
        toast("Failed to fetch leads", {
          description: "Unable to load leads. Please try again."
        });
      }
    };
    fetchLeads();

    const fetchCampaigns = async () => {
      try {
        const userId = await authApi.getUserId();
        const response = await crmApi.getCampaigns(userId);
        setCampaigns(response.campaigns || response || []);
      } catch (error) {
        toast("Failed to fetch campaigns", {
          description: "Unable to load campaigns. Please try again."
        });
      }
    };
    fetchCampaigns();
  }, []);

  // Fetch templates when dialog opens
  useEffect(() => {
    if (!isDialogOpen) return;
    const fetchTemplates = async () => {
      try {
        const userId = await authApi.getUserId();
        const response = await crmApi.getOutreachTemplates(userId);
        setTemplates(response || []);
      } catch (error) {
        toast("Failed to fetch templates", {
          description: "Unable to load templates. Please try again."
        });
      }
    };
    fetchTemplates();
  }, [isDialogOpen]);

  // When template is selected, fill message_content and subject
  useEffect(() => {
    if (!selectedTemplate || selectedTemplate === "none") return;
    const template = templates.find(t => t.id.toString() === selectedTemplate);
    if (template) {
      setForm(f => ({ ...f, message_content: template.content, subject: template.subject || "", template_id: template.id.toString() }));
    }
  }, [selectedTemplate, templates]);

  // Lead search for multi-select
  useEffect(() => {
    if (leadSearchTerm.trim() === "") {
      setFilteredLeads([]);
      return;
    }
    const searchTermLower = leadSearchTerm.toLowerCase();
    setFilteredLeads(
      leads.filter(
        (lead) =>
          (lead.full_name?.toLowerCase().includes(searchTermLower) ||
            lead.email?.toLowerCase().includes(searchTermLower) ||
            lead.company?.toLowerCase().includes(searchTermLower)) &&
          !selectedLeads.some((l) => l.id === lead.id)
      )
    );
  }, [leadSearchTerm, leads, selectedLeads]);

  // Form logic: if campaign is selected, clear leads; if leads are selected, clear campaign
  useEffect(() => {
    if (selectedCampaign && selectedCampaign !== "none") setSelectedLeads([]);
  }, [selectedCampaign]);
  useEffect(() => {
    if (selectedLeads.length > 0) setSelectedCampaign("none");
  }, [selectedLeads]);

  const handleAddLead = (lead: Lead) => {
    setSelectedLeads((prev) => [...prev, lead]);
    setLeadSearchTerm("");
  };
  const handleRemoveLead = (leadId: number) => {
    setSelectedLeads((prev) => prev.filter((l) => l.id !== leadId));
  };

  const handleSendEmail = async () => {
    if (!form.message_content.trim()) {
      toast("Message content is required");
      return;
    }
    if ((selectedCampaign === "none" || !selectedCampaign) && selectedLeads.length === 0) {
      toast("Select at least one lead or a campaign");
      return;
    }
    setIsSubmitting(true);
    try {
      const body = {
        lead_ids: selectedLeads.length > 0 ? selectedLeads.map((l) => l.id) : [],
        platform_id: parseInt(form.platform_id),
        message_content: form.message_content,
        subject: form.subject || null,
        template_id: form.template_id ? parseInt(form.template_id) : null,
        campaign_id: selectedCampaign && selectedCampaign !== "none" ? parseInt(selectedCampaign) : null,
      };
      const userId = await authApi.getUserId();
      const response = await crmApi.sendMessage(userId, body);
      toast("Message(s) sent", {
        description: `Success: ${response.success_count}, Failed: ${response.failed_count}`,
      });
      setIsDialogOpen(false);
      setForm({ platform_id: "1", message_content: "", subject: "", template_id: "" });
      setSelectedLeads([]);
      setSelectedCampaign("none");
      fetchBulkGroups();
    } catch (error) {
      toast("Failed to send message(s)", {
        description: error instanceof Error ? error.message : "An error occurred. Please try again.",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const handlePrevPage = () => {
    if (page > 1) setPage(page - 1);
  };
  const handleNextPage = () => {
    if (page < totalPages) setPage(page + 1);
  };
  const handlePageSelect = (p: number) => {
    if (p !== page && p >= 1 && p <= totalPages) setPage(p);
  };

  // Update dialog open handler to fetch data
  const handleOpenBulkGroupDialog = async (bulkGroupId: number) => {
    setIsBulkGroupDialogOpen(true);
    setDialogLoading(true);
    setDialogBulkGroup(null);
    setDialogMessages([]);
    try {
      const userId = await authApi.getUserId();
      // Fetch the latest bulk group details
      const groups = await crmApi.getBulkMessageGroups(userId);
      const group = groups.find((g: BulkMessageGroup) => g.id === bulkGroupId) || null;
      setDialogBulkGroup(group);
      // Fetch the latest messages for this group
      const messagesResp = await crmApi.getOutreachMessages(userId, { bulk_group_id: bulkGroupId });
      setDialogMessages(messagesResp.results || messagesResp || []);
    } catch (err) {
      setDialogBulkGroup(null);
      setDialogMessages([]);
    } finally {
      setDialogLoading(false);
    }
  };

  // Remove groupedMessages and any use of messages/allMessages in render
  // The main table should use bulkGroups directly
  // Remove any Table or UI code that references groupedMessages or messages

  // Edit message handler
  const handleEditMessage = (message: OutreachMessage) => {
    setEditMessage(message);
    setEditMessageContent(message.message_content);
    setIsEditDialogOpen(true);
  };

  const handleSaveEditMessage = async () => {
    if (!editMessage) return;
    try {
      const userId = await authApi.getUserId();
      await crmApi.updateOutreachMessage(userId, editMessage.id, { message_content: editMessageContent });
      // Refresh messages in dialog
      if (dialogBulkGroup) await handleOpenBulkGroupDialog(dialogBulkGroup.id);
      setIsEditDialogOpen(false);
      setEditMessage(null);
    } catch (err) {
      toast("Failed to update message", { description: err instanceof Error ? err.message : "An error occurred." });
    }
  };

  // Delete message handler
  const handleDeleteMessage = (messageId: number) => {
    setDeleteMessageId(messageId);
    setIsDeleteDialogOpen(true);
  };

  const confirmDeleteMessage = async () => {
    if (!deleteMessageId) return;
    try {
      const userId = await authApi.getUserId();
      await crmApi.deleteOutreachMessage(userId, deleteMessageId);
      // Refresh messages in dialog
      if (dialogBulkGroup) await handleOpenBulkGroupDialog(dialogBulkGroup.id);
      setIsDeleteDialogOpen(false);
      setDeleteMessageId(null);
    } catch (err) {
      toast("Failed to delete message", { description: err instanceof Error ? err.message : "An error occurred." });
    }
  };

  if (error) {
    return (
      <div className="p-6 text-center">
        <p className="text-red-500">Error: {error}</p>
        <Button 
          onClick={() => window.location.reload()} 
          className="mt-4 bg-black text-white hover:bg-gray-800"
        >
          Retry
        </Button>
      </div>
    );
  }

  // if (isLoading) {
  //   return (
  //     <div className="p-6 text-center">
  //       <Loader2 className="w-6 h-6 animate-spin mx-auto mb-2" />
  //       <p>Loading...</p>
  //     </div>
  //   );
  // }

  return (
    <div className="p-6  min-h-screen">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-black">Outreach Conversations</h1>
            <p className="text-gray-600">View and manage your outreach messages</p>
          </div>
          <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
            <DialogTrigger asChild>
              <Button className="bg-black text-white hover:bg-gray-800">
                <Plus className="w-4 h-4 mr-2" />
                Send Message
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-[500px]">
              <DialogHeader>
                <DialogTitle>Send Message</DialogTitle>
                <DialogDescription>
                  Send a message to multiple leads or a campaign. If you select a campaign, you cannot select leads and vice versa.
                </DialogDescription>
              </DialogHeader>
              <div className="grid gap-4 py-4">
                {/* Platform Selection */}
                <div>
                  <Label className="text-sm font-medium mb-1 block">Platform *</Label>
                  <Select
                    value={form.platform_id}
                    onValueChange={(value) => setForm((f) => ({ ...f, platform_id: value }))}
                  >
                    <SelectTrigger className=" rounded-2xl">
                      <SelectValue placeholder="Select platform" />
                    </SelectTrigger>
                    <SelectContent className="rounded-2xl">
                      {platforms.map((platform) => (
                        <SelectItem key={platform.id} value={platform.id.toString()}>
                          {platform.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                {/* Campaign Selection */}
                <div>
                  <Label className="text-sm font-medium mb-1 block">Campaign</Label>
                  <Select
                    value={selectedCampaign}
                    onValueChange={setSelectedCampaign}
                    disabled={selectedLeads.length > 0}
                  >
                    <SelectTrigger className=" rounded-2xl">
                      <SelectValue placeholder="Select campaign (optional)" />
                    </SelectTrigger>
                    <SelectContent className="rounded-2xl">
                      <SelectItem value="none">None</SelectItem>
                      {campaigns
                        .filter((campaign) => campaign.id)
                        .map((campaign) => (
                          <SelectItem key={campaign.id} value={campaign.id.toString()}>
                            {campaign.name}
                          </SelectItem>
                        ))}
                    </SelectContent>
                  </Select>
                </div>  
                {/* Template Selection */}
                <div>
                  <Label className="text-sm font-medium mb-1 block">Template</Label>
                  <Select
                    value={selectedTemplate}
                    onValueChange={setSelectedTemplate}
                  >
                    <SelectTrigger className=" rounded-2xl">
                      <SelectValue placeholder="Select template (optional)" />
                    </SelectTrigger>
                    <SelectContent className="rounded-2xl">
                      <SelectItem value="none">None</SelectItem>
                      {templates.map((template) => (
                        <SelectItem key={template.id} value={template.id.toString()}>
                          {template.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                {/* Subject */}
                <div>
                  <Label className="text-sm font-medium mb-1 block">Subject</Label>
                  <Input
                    type="text"
                    value={form.subject}
                    onChange={(e) => setForm((f) => ({ ...f, subject: e.target.value }))}
                    placeholder="Enter subject (optional for email)"
                    className=" focus:ring-black rounded-2xl"
                  />
                </div>
                {/* Message Content */}
                <div>
                  <Label className="text-sm font-medium mb-1 block">Message Content *</Label>
                  <Textarea
                    value={form.message_content}
                    onChange={(e) => setForm((f) => ({ ...f, message_content: e.target.value }))}
                    placeholder="Enter your message"
                    className=" focus:ring-black rounded-2xl min-h-32"
                  />
                </div>
                {/* Lead Multi-Select Search */}
                {/* <div>
                  <Label className="text-sm font-medium mb-1 block">Leads</Label>
                  <div className="relative">
                    <Input
                      type="text"
                      value={leadSearchTerm}
                      onChange={(e) => setLeadSearchTerm(e.target.value)}
                      placeholder="Search leads by name, email, company..."
                      className=" focus:ring-black rounded-2xl pr-10"
                      disabled={!!selectedCampaign}
                    />
                    {leadSearchTerm && filteredLeads.length > 0 && !selectedCampaign && (
                      <div className="absolute z-50 mt-1 w-full rounded-2xl shadow-lg border border-gray-200 max-h-60 overflow-auto">
                        <div className="p-2">
                          {filteredLeads.map((lead) => (
                            <button
                              key={lead.id}
                              type="button"
                              onClick={(e) => {
                                e.stopPropagation();
                                handleAddLead(lead);
                              }}
                              className="w-full text-left px-3 py-2 hover:bg-gray-100 rounded-md transition-colors flex flex-col"
                            >
                              <span className="font-medium text-black">{lead.full_name}</span>
                              <span className="text-sm text-gray-600">
                                {lead.company} • {lead.email}
                              </span>
                            </button>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                  <div className="flex flex-wrap gap-2 mt-2">
                    {selectedLeads.map((lead) => (
                      <span key={lead.id} className="flex items-center bg-gray-200 rounded-2xl px-2 py-1 text-xs text-black">
                        {lead.full_name || lead.email}
                        <button
                          type="button"
                          className="ml-1 text-gray-600 hover:text-gray-800"
                          onClick={() => handleRemoveLead(lead.id)}
                        >
                          <X className="h-3 w-3" />
                        </button>
                      </span>
                    ))}
                  </div>
                </div> */}
              </div> 
              <DialogFooter>
                <Button
                  variant="outline"
                  className="rounded-2xl border-0 bg-muted/50"
                  onClick={() => setIsDialogOpen(false)}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  onClick={handleSendEmail}
                  className="bg-black text-white hover:bg-gray-800 rounded-2xl"
                  disabled={isSubmitting || !form.platform_id || !form.message_content || (selectedLeads.length === 0 && selectedCampaign === "none")}
                >
                  {isSubmitting ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Sending...
                    </>
                  ) : (
                    'Send Message'
                  )}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>

        {/* Filters */}
        {/* <Card className="border ">
          <CardHeader>
            <CardTitle className="text-black">Filters</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex gap-4">
              <div className="flex-1">
                <div className="relative">
                  <Search className="absolute left-3 top-3 h-4 w-4 text-gray-600" />
                  <Input
                    placeholder="Search messages..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="pl-10  rounded-2xl"
                  />
                </div>
              </div>
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger className="w-48  rounded-2xl">
                  <SelectValue placeholder="Filter by status" />
                </SelectTrigger>
                <SelectContent className="  rounded-2xl">
                  <SelectItem value="all">All Statuses</SelectItem>
                  <SelectItem value="sent">Sent</SelectItem>
                  <SelectItem value="failed">Failed</SelectItem>
                  <SelectItem value="delivered">Delivered</SelectItem>
                  <SelectItem value="read">Read</SelectItem>
                </SelectContent>
              </Select>
              <Select value={platformFilter} onValueChange={setPlatformFilter}>
                <SelectTrigger className="w-48  rounded-2xl">
                  <SelectValue placeholder="Filter by platform" />
                </SelectTrigger>
                <SelectContent className="  rounded-2xl">
                  <SelectItem value="all">All Platforms</SelectItem>
                  {platforms.map((platform) => (
                    <SelectItem key={platform.id} value={platform.id.toString()}>
                      {platform.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </CardContent>
        </Card> */}

        {/* Bulk Messages Table */}
        <Card className="border ">
          <CardHeader>
          <div className="flex items-center justify-between">
              <CardTitle>
                Messages ({bulkGroups.length})
                {isLoading && <Loader2 className="ml-2 h-4 w-4 animate-spin inline" />}
              </CardTitle>
              <div className="relative w-[300px]">
                <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search campaigns..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10 rounded-2xl border-0 bg-muted/50"
                />
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="text-black">Subject</TableHead>
                  <TableHead className="text-black">Platform</TableHead>
                  <TableHead className="text-black">Total Leads</TableHead>
                  <TableHead className="text-black">Success</TableHead>
                  <TableHead className="text-black">Failed</TableHead>
                  <TableHead className="text-black">Sent At</TableHead>
                  <TableHead className="text-black">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {isLoading ? (
                  [...Array(5)].map((_, i) => (
                    <TableRow key={i}>
                      {[...Array(7)].map((_, j) => (
                        <TableCell key={j}><Skeleton className="h-4 w-24" /></TableCell>
                      ))}
                    </TableRow>
                  ))
                ) : bulkGroups.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={7} className="text-center text-muted-foreground py-6">
                      No bulk messages found
                    </TableCell>
                  </TableRow>
                ) : (
                  bulkGroups.map((group) => (
                    <TableRow
                      key={group.id}
                      className="cursor-pointer hover:bg-gray-50"
                      onClick={() => handleOpenBulkGroupDialog(group.id)}
                    >
                      <TableCell className="text-black font-medium">{group.subject || "N/A"}</TableCell>
                      <TableCell className="text-black">{group.platform?.name || "Unknown"}</TableCell>
                      <TableCell className="text-black">{group.total_leads}</TableCell>
                      <TableCell className="text-black">{group.success_count}</TableCell>
                      <TableCell className="text-black">{group.failed_count}</TableCell>
                      <TableCell className="text-black">{formatDate(group.created_at)}</TableCell>
                      <TableCell>
                        <div className="flex gap-2">
                          <Button
                            size="sm"
                            variant="outline"
                            className="text-destructive hover:bg-destructive/10 rounded-2xl"
                            onClick={(e) => {
                              e.stopPropagation();
                              setDeleteMessageId(group.id);
                              setIsDeleteDialogOpen(true);
                            }}
                          >
                            Delete
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>

            </Table>
            {bulkGroups.length === 0 && !isLoading && (
              <p className="text-gray-500 text-center py-8">No bulk messages found</p>
            )}
          </CardContent>
        </Card>

        {/* Bulk Group Dialog */}
        <Dialog open={isBulkGroupDialogOpen} onOpenChange={setIsBulkGroupDialogOpen}>
          <DialogContent className="sm:max-w-[600px] rounded-2xl">
            <DialogHeader>
              <DialogTitle>Message Details</DialogTitle>
              <DialogDescription>
                Details of all recipients for this message
              </DialogDescription>
            </DialogHeader>
            <div className="mt-4">
              {dialogLoading ? (
                <div className="text-center py-8">Loading...</div>
              ) : dialogBulkGroup ? (
                <>
                  <div className="space-y-4">
                    <div>
                      <Label className="text-sm text-gray-600">Subject</Label>
                      <p className="text-black">{dialogBulkGroup.subject || 'N/A'}</p>
                    </div>
                    <div>
                      <Label className="text-sm text-gray-600">Content</Label>
                      <div className="bg-muted/50 p-4 rounded-2xl mt-1">
                        <p className="whitespace-pre-wrap text-black">
                          {dialogMessages.map(m => m.message_content).join('\n\n') || 'N/A'}
                        </p>
                      </div>
                    </div>
                    <div>
                      <Label className="text-sm text-gray-600">Recipients</Label>
                      <Table>
                        <TableHeader>
                          <TableRow>
                            <TableHead className="text-black">Lead ID</TableHead>
                            <TableHead className="text-black">Lead Name</TableHead>
                            <TableHead className="text-black">Status</TableHead>
                            <TableHead className="text-black">Sent At</TableHead>
                            <TableHead className="text-black">Actions</TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {dialogMessages.map((message) => {
                            const lead = leads.find(l => l.id === message.lead_id);
                            return (
                              <TableRow key={message.id}>
                                <TableCell className="text-black">{message.lead_id}</TableCell>
                                <TableCell className="text-black">{lead?.full_name || 'N/A'}</TableCell>
                                <TableCell>
                                  <Badge
                                    variant={message.status === 'sent' || message.status === 'delivered' ? 'default' : 'destructive'}
                                    className={message.status === 'sent' || message.status === 'delivered' ? 'bg-green-600' : ''}
                                  >
                                    {message.status}
                                  </Badge>
                                </TableCell>
                                <TableCell className="text-black">
                                  {message.sent_at ? formatDate(message.sent_at) : 'N/A'}
                                </TableCell>
                                <TableCell>
                                  <div className="flex gap-2">
                                    {/* <Button size="sm" variant="outline" onClick={() => handleEditMessage(message)}>Edit</Button> */}
                                    <Button size="sm" variant="outline" className="text-destructive" onClick={() => handleDeleteMessage(message.id)}>Delete</Button>
                                  </div>
                                </TableCell>
                              </TableRow>
                            );
                          })}
                        </TableBody>
                      </Table>
                    </div>
                    {dialogBulkGroup.failed_count > 0 && (
                      <div className="mt-4 flex justify-end">
                        <Button
                          variant="outline"
                          className=" rounded-2xl"
                          onClick={() => {
                            // handleResendFailedMessages(dialogBulkGroup.id); // This function is not defined in the main table
                            setIsBulkGroupDialogOpen(false);
                          }}
                        >
                          Resend Failed
                        </Button>
                      </div>
                    )}
                  </div>
                </>
              ) : (
                <div className="text-center py-8">No data found.</div>
              )}
            </div>
          </DialogContent>
        </Dialog>

        {/* Edit Message Dialog */}
        {/* <Dialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Edit Message</DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <Label>Message Content</Label>
              <textarea
                className="w-full min-h-[100px] p-2 border rounded-md"
                value={editMessageContent}
                onChange={e => setEditMessageContent(e.target.value)}
              />
              <div className="flex gap-2 justify-end">
                <Button onClick={handleSaveEditMessage} className="bg-black text-white">Save</Button>
                <Button variant="outline" onClick={() => setIsEditDialogOpen(false)}>Cancel</Button>
              </div>
            </div>
          </DialogContent>
        </Dialog> */}

        {/* Delete Message Confirmation Dialog */}
        <Dialog open={isDeleteDialogOpen} onOpenChange={setIsDeleteDialogOpen}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Confirm Delete</DialogTitle>
            </DialogHeader>
            <div className="py-4">Are you sure you want to delete this message?</div>
            <div className="flex gap-2 justify-end">
              <Button variant="outline" onClick={() => setIsDeleteDialogOpen(false)}>Cancel</Button>
              <Button className="bg-red-600 text-white" onClick={confirmDeleteMessage}>Delete</Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
}