import { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import { Send, Calendar, Edit, MessageSquare, Loader2 } from "lucide-react";
import { toast } from "@/hooks/use-toast";
import { crmApi } from "@/lib/crmAPI";
import { authApi, ConversationDetails as IConversationDetails } from "@/lib/api";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { calendarApi } from "@/lib/calendarApi";
import { leadApi } from "@/lib/leadApi";

// Updated ConversationMessage type to match new API response
type ConversationMessage = {
  conversation_id: number;
  direction: "incoming" | "outgoing";
  message_content: string;
  sender_identifier: string;
  recipient_identifier: string;
  id: number;
  outreach_message_id: number | null;
  sent_at: string;
  platform_message_id: string | null;
  created_at: string;
  updated_at: string;
};

export default function ConversationDetails() {
  const { conversationId } = useParams();
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [conversation, setConversation] = useState<IConversationDetails | null>(null);
  const [messages, setMessages] = useState<ConversationMessage[]>([]);
  const [newMessage, setNewMessage] = useState({
    message_content: "",
    direction: "outgoing" as "incoming" | "outgoing",
    sender_identifier: "agent_123",
    recipient_identifier: "lead_456"
  });
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [editForm, setEditForm] = useState({
    status: "open",
    subject: "",
  });

  // Create Lead Event Dialog State
  const [eventDialogOpen, setEventDialogOpen] = useState(false);
  const [eventForm, setEventForm] = useState({
    title: "",
    description: "",
    meeting_url: "",
    start_datetime: "",
    end_datetime: "",
    notes: "",
    event_type: "meeting",
  });
  const [isEventSubmitting, setIsEventSubmitting] = useState(false);

  const eventTypeOptions = [
    { value: "meeting", label: "Meeting" },
    { value: "call", label: "Call" },
    { value: "appointment", label: "Appointment" },
    { value: "demo", label: "Demo" },
    { value: "presentation", label: "Presentation" },
    { value: "consultation", label: "Consultation" },
    { value: "negotiation", label: "Negotiation" },
    { value: "closing", label: "Closing" },
    { value: "follow_up", label: "Follow Up" },
    { value: "initial_call", label: "Initial Call" },
    { value: "discovery", label: "Discovery" },
    { value: "proposal", label: "Proposal" },
    { value: "contract_review", label: "Contract Review" },
    { value: "onboarding", label: "Onboarding" },
    { value: "check_in", label: "Check In" },
    { value: "training", label: "Training" },
    { value: "support", label: "Support" },
    { value: "other", label: "Other" },
  ];

  const [lead, setLead] = useState(null);
  const userId = authApi.getUserId();
  useEffect(() => {
    const fetchConversationAndMessages = async () => {
      if (!conversationId) return;

      try {
        setIsLoading(true);
        setError(null);
        const [conversationRes, messagesRes] = await Promise.all([
          crmApi.getConversation(Number(conversationId)),
          crmApi.getConversationMessages(Number(conversationId)),
        ]);
        setConversation(conversationRes as IConversationDetails);
        setMessages(messagesRes as ConversationMessage[]);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch conversation');
        toast({
          variant: "destructive",
          title: "Error",
          description: "Failed to fetch conversation details. Please try again.",
        });
      } finally {
        setIsLoading(false);
      }
    };

    fetchConversationAndMessages();
  }, [conversationId]);

  useEffect(() => {
    if (conversation) {
      setEditForm({
        status: conversation.status,
        subject: conversation.subject,
      });
    }
  }, [conversation]);

  useEffect(() => {
    if (conversation && conversation.lead_id) {
      leadApi.getLead(conversation.lead_id).then(setLead);
    }
  }, [conversation]);

  const handleSendMessage = async () => {
    if (!newMessage.message_content.trim() || !conversationId) return;

    // Prepare the message body as per the new API contract
    const messageData = {
      conversation_id: Number(conversationId),
      direction: newMessage.direction,
      message_content: newMessage.message_content,
      sender_identifier: newMessage.sender_identifier,
      recipient_identifier: newMessage.recipient_identifier,
      outreach_message_id: null,
      platform_message_id: null
    };

    try {
      const newMessageResponse = await crmApi.createConversationMessage(Number(conversationId), messageData);
      setMessages(prev => [...prev, newMessageResponse]);
      setNewMessage(prev => ({ ...prev, message_content: "" }));
      toast({
        title: "Message Sent",
        description: "Your message has been sent successfully.",
      });
    } catch (err) {
      toast({
        variant: "destructive",
        title: "Error",
        description: "Failed to send message. Please try again.",
      });
    }
  };

  const handleCloseConversation = async () => {
    if (!conversationId) return;

    try {
      await crmApi.closeConversation(Number(conversationId));
      setConversation(prev => prev ? { ...prev, status: "closed" } : null);
      toast({
        title: "Conversation Closed",
        description: "The conversation has been closed.",
      });
    } catch (err) {
      toast({
        variant: "destructive",
        title: "Error",
        description: "Failed to close conversation. Please try again.",
      });
    }
  };

  const handleReopenConversation = async () => {
    if (!conversationId) return;
    try {
      await crmApi.reopenConversation(Number(conversationId));
      setConversation(prev => prev ? { ...prev, status: "open" } : null);
      toast({
        title: "Conversation Reopened",
        description: "The conversation has been reopened.",
      });
    } catch (err) {
      toast({
        variant: "destructive",
        title: "Error",
        description: "Failed to reopen conversation. Please try again.",
      });
    }
  };

  const handleUpdateConversation = async () => {
    if (!conversationId) return;
    try {
      const response = await crmApi.updateConversation(Number(conversationId), {
        status: editForm.status,
        subject: editForm.subject,
      });
      setConversation(response);
      setEditDialogOpen(false);
      toast({
        title: "Conversation Updated",
        description: "The conversation details have been updated.",
      });
    } catch (err) {
      toast({
        variant: "destructive",
        title: "Error",
        description: "Failed to update conversation. Please try again.",
      });
    }
  };

  const handleCreateEvent = async () => {
    if (!conversation || !conversation.lead_id) return;
    setIsEventSubmitting(true);
    try {
      // Compose the event body with all required and relevant info
      const eventBody = {
        title: eventForm.title,
        description: eventForm.description,
        start_datetime: eventForm.start_datetime,
        end_datetime: eventForm.end_datetime,
        event_type: eventForm.event_type,
        priority: "high",
        location: "",
        meeting_url: eventForm.meeting_url,
        timezone: "America/New_York",
        lead_id: conversation.lead_id,
        deal_value: undefined,
        deal_stage: undefined,
        reminder_minutes: [15],
        notes: eventForm.notes,
        tags: "conversation,lead",
        attendees: lead ? [
          {
            name: lead.full_name || "",
            email: lead.email || "",
            phone: lead.phone || "",
            company: lead.company || "",
            job_title: lead.job_title || "",
            lead_id: lead.id,
            is_organizer: false,
            is_required: true,
            user_id: userId.toString()
          }
        ] : [],
        user_id: userId.toString()
      };
      await calendarApi().createEvent(eventBody);
      toast({
        title: "Event Created",
        description: "Lead event has been created successfully.",
      });
      setEventDialogOpen(false);
      setEventForm({
        title: "",
        description: "",
        meeting_url: "",
        start_datetime: "",
        end_datetime: "",
        notes: "",
        event_type: "meeting",
      });
    } catch (err) {
      toast({
        variant: "destructive",
        title: "Error",
        description: "Failed to create event. Please try again.",
      });
    } finally {
      setIsEventSubmitting(false);
    }
  };

  const formatTime = (dateString: string) => {
    return new Date(dateString).toLocaleString();
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

  if (isLoading || !conversation) {
    return (
      <div className="p-6  min-h-screen flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  return (
    <div className="p-6  min-h-screen">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-black">{conversation.subject}</h1>
            <p className="text-gray-600">Conversation with Lead #{conversation.lead_id}</p>
          </div>
          
          <div className="flex gap-3">
            <Dialog open={editDialogOpen} onOpenChange={setEditDialogOpen}>
              <DialogTrigger asChild>
                <Button variant="outline" className="border-black text-black hover:bg-gray-100">
                  <Edit className="w-4 h-4 mr-2" />
                  Edit Conversation
                </Button>
              </DialogTrigger>
              <DialogContent className="sm:max-w-[425px]">
                <DialogHeader>
                  <DialogTitle>Edit Conversation</DialogTitle>
                  <DialogDescription>
                    Update the subject and status of this conversation.
                  </DialogDescription>
                </DialogHeader>
                <div className="grid gap-4 py-4">
                  <div>
                    <label className="text-sm font-medium mb-1 block">Subject *</label>
                    <Input
                      type="text"
                      value={editForm.subject}
                      onChange={e => setEditForm({ ...editForm, subject: e.target.value })}
                      placeholder="Enter conversation subject"
                      className="border-black focus:ring-black"
                    />
                  </div>
                  <div>
                    <label className="text-sm font-medium mb-1 block">Status *</label>
                    <Select
                      value={editForm.status}
                      onValueChange={value => setEditForm({ ...editForm, status: value })}
                    >
                      <SelectTrigger className="border-black">
                        <SelectValue placeholder="Select status" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="open">Open</SelectItem>
                        <SelectItem value="closed">Closed</SelectItem>
                        <SelectItem value="pending_reply">Pending Reply</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <DialogFooter>
                  <Button
                    type="button"
                    className="bg-black text-white hover:bg-gray-800"
                    onClick={handleUpdateConversation}
                  >
                    Update Conversation
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
            {conversation.status === "closed" ? (
              <Button
                variant="outline"
                className="border-green-500 text-green-500 hover:bg-green-50"
                onClick={handleReopenConversation}
              >
                Reopen Conversation
              </Button>
            ) : (
              <Button
                variant="outline"
                className="border-red-500 text-red-500 hover:bg-red-50"
                onClick={handleCloseConversation}
              >
                Close Conversation
              </Button>
            )}
            <Dialog open={eventDialogOpen} onOpenChange={setEventDialogOpen}>
              <DialogTrigger asChild>
                <Button variant="outline" className="border-black text-black hover:bg-gray-100">
                  <Calendar className="w-4 h-4 mr-2" />
                  Create Lead Event
                </Button>
              </DialogTrigger>
              <DialogContent className="sm:max-w-[425px]">
                <DialogHeader>
                  <DialogTitle>Create Lead Event</DialogTitle>
                  <DialogDescription>
                    Schedule a new event for this lead.
                  </DialogDescription>
                </DialogHeader>
                <div className="grid gap-4 py-4">
                  <div>
                    <label className="text-sm font-medium mb-1 block">Title *</label>
                    <Input
                      type="text"
                      value={eventForm.title}
                      onChange={e => setEventForm({ ...eventForm, title: e.target.value })}
                      placeholder="Enter event title"
                      className="border-black focus:ring-black"
                    />
                  </div>
                  <div>
                    <label className="text-sm font-medium mb-1 block">Description</label>
                    <Textarea
                      value={eventForm.description}
                      onChange={e => setEventForm({ ...eventForm, description: e.target.value })}
                      placeholder="Enter event description"
                      className="border-black focus:ring-black"
                    />
                  </div>
                  <div>
                    <label className="text-sm font-medium mb-1 block">Meeting URL</label>
                    <Input
                      type="text"
                      value={eventForm.meeting_url}
                      onChange={e => setEventForm({ ...eventForm, meeting_url: e.target.value })}
                      placeholder="https://..."
                      className="border-black focus:ring-black"
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <label className="text-sm font-medium mb-1 block">Start Time *</label>
                      <Input
                        type="datetime-local"
                        value={eventForm.start_datetime}
                        onChange={e => setEventForm({ ...eventForm, start_datetime: e.target.value })}
                        className="border-black focus:ring-black"
                      />
                    </div>
                    <div>
                      <label className="text-sm font-medium mb-1 block">End Time *</label>
                      <Input
                        type="datetime-local"
                        value={eventForm.end_datetime}
                        onChange={e => setEventForm({ ...eventForm, end_datetime: e.target.value })}
                        className="border-black focus:ring-black"
                      />
                    </div>
                  </div>
                  <div>
                    <label className="text-sm font-medium mb-1 block">Notes</label>
                    <Textarea
                      value={eventForm.notes}
                      onChange={e => setEventForm({ ...eventForm, notes: e.target.value })}
                      placeholder="Enter notes"
                      className="border-black focus:ring-black"
                    />
                  </div>
                  <div>
                    <label className="text-sm font-medium mb-1 block">Event Type *</label>
                    <Select
                      value={eventForm.event_type}
                      onValueChange={value => setEventForm({ ...eventForm, event_type: value })}
                    >
                      <SelectTrigger className="border-black">
                        <SelectValue placeholder="Select event type" />
                      </SelectTrigger>
                      <SelectContent>
                        {eventTypeOptions.map(opt => (
                          <SelectItem key={opt.value} value={opt.value}>{opt.label}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <DialogFooter>
                  <Button
                    type="button"
                    className="bg-black text-white hover:bg-gray-800"
                    onClick={handleCreateEvent}
                    disabled={isEventSubmitting}
                  >
                    {isEventSubmitting ? "Creating..." : "Create Event"}
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </div>
        </div>

        <div className="grid lg:grid-cols-3 gap-6">
          {/* Conversation Details */}
          <div className="lg:col-span-1">
            <Card className="border border-black">
              <CardHeader>
                <CardTitle className="text-black">Conversation Details</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <h4 className="font-semibold text-black">Lead ID</h4>
                  <p className="text-gray-700">#{conversation.lead_id}</p>
                </div>
                <div>
                  <h4 className="font-semibold text-black">Platform</h4>
                  <p className="text-gray-700">{conversation.platform.name}</p>
                </div>
                <div>
                  <h4 className="font-semibold text-black">Status</h4>
                  <span className={`px-2 py-1 rounded text-xs ${
                    conversation.status === 'open' 
                      ? 'bg-blue-100 text-blue-800' 
                      : conversation.status === 'closed'
                      ? 'bg-gray-100 text-gray-800'
                      : 'bg-orange-100 text-orange-800'
                  }`}>
                    {conversation.status}
                  </span>
                </div>
                <div>
                  <h4 className="font-semibold text-black">Created</h4>
                  <p className="text-gray-700">{formatTime(conversation.created_at)}</p>
                </div>
                <div>
                  <h4 className="font-semibold text-black">Last Updated</h4>
                  <p className="text-gray-700">{formatTime(conversation.updated_at)}</p>
                </div>
                {conversation.last_message_at && (
                  <div>
                    <h4 className="font-semibold text-black">Last Message</h4>
                    <p className="text-gray-700">{formatTime(conversation.last_message_at)}</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Messages and Input */}
          <div className="lg:col-span-2 space-y-6">
            {/* Messages List */}
            <Card className="border border-black">
              <CardHeader>
                <CardTitle className="text-black flex items-center gap-2">
                  <MessageSquare className="w-5 h-5" />
                  Messages ({messages.length})
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4 max-h-96 overflow-y-auto">
                  {messages.map((message) => (
                    <div
                      key={message.id}
                      className={`flex ${message.direction === 'outgoing' ? 'justify-end' : 'justify-start'}`}
                    >
                      <div className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                        message.direction === 'outgoing'
                          ? 'bg-black text-white'
                          : 'bg-gray-100 text-black'
                      }`}>
                        <p className="text-sm">{message.message_content}</p>
                        <p className={`text-xs mt-1 ${
                          message.direction === 'outgoing' ? 'text-gray-300' : 'text-gray-500'
                        }`}>
                          {formatTime(message.sent_at)}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Message Input */}
            <Card className="border border-black">
              <CardHeader>
                <CardTitle className="text-black">Send Message</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <Label htmlFor="direction" className="text-black">Direction</Label>
                  <Select 
                    value={newMessage.direction} 
                    onValueChange={(value: "incoming" | "outgoing") => setNewMessage(prev => ({ ...prev, direction: value }))}
                  >
                    <SelectTrigger className="border-black">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className=" border-black">
                      <SelectItem value="outgoing">Outgoing</SelectItem>
                      <SelectItem value="incoming">Incoming</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label htmlFor="message" className="text-black">Message</Label>
                  <Textarea
                    id="message"
                    value={newMessage.message_content}
                    onChange={(e) => setNewMessage(prev => ({ ...prev, message_content: e.target.value }))}
                    className="border-black min-h-24"
                    placeholder="Type your message..."
                  />
                </div>
                <Button 
                  onClick={handleSendMessage}
                  className="bg-black text-white hover:bg-gray-800"
                  disabled={!newMessage.message_content.trim()}
                >
                  <Send className="w-4 h-4 mr-2" />
                  Send Message
                </Button>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}