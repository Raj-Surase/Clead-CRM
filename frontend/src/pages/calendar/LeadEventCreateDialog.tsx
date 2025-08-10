import { useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import { calendarApi } from "@/lib/calendarApi";
import { Lead } from "@/lib/api";
import { authApi } from "@/lib/authApi";

const defaultEventType = "meeting";
const defaultPriority = "low";

export default function LeadEventCreateDialog({ open, onOpenChange, lead, onEventCreated }: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  lead: Lead | null;
  onEventCreated: () => void;
}) {
  const [form, setForm] = useState({
    title: "",
    description: "",
    date: "",
    start_time: "",
    duration: 30,
    event_type: defaultEventType,
    priority: defaultPriority,
    location: "",
    meeting_url: "",
    notes: "",
  });
  const [isLoading, setIsLoading] = useState(false);
  const userId = authApi.getUserId();
  // Prefill lead details and attendee
  const attendee = lead ? [{
    name: lead.full_name || "",
    email: lead.email || "",
    phone: lead.phone || "",
    company: lead.company || "",
    job_title: lead.job_title || "",
    lead_id: lead.id,
    is_organizer: false,
    is_required: true,
    user_id: userId.toString()
  }] : [];

  const handleChange = (field: string, value: any) => {
    setForm(prev => ({ ...prev, [field]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!lead) return;
    if (!form.title || !form.date || !form.start_time) {
      toast.error("Please fill in all required fields");
      return;
    }
    setIsLoading(true);
    try {
      const startDateTime = new Date(`${form.date}T${form.start_time}`);
      if (isNaN(startDateTime.getTime())) throw new Error("Invalid start date/time");
      const endDateTime = new Date(startDateTime.getTime() + (form.duration * 60000));
      const api = calendarApi();
      await api.createEvent({
        title: form.title,
        description: form.description,
        start_datetime: startDateTime.toISOString(),
        end_datetime: endDateTime.toISOString(),
        event_type: form.event_type,
        priority: form.priority,
        location: form.location,
        meeting_url: form.meeting_url,
        notes: form.notes,
        lead_id: lead.id,
        attendees: attendee,
        user_id: userId.toString()
      });
      toast.success("Event created successfully");
      onEventCreated();
      setForm({
        title: "",
        description: "",
        date: "",
        start_time: "",
        duration: 30,
        event_type: defaultEventType,
        priority: defaultPriority,
        location: "",
        meeting_url: "",
        notes: "",
      });
    } catch (err) {
      toast.error("Failed to create event");
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  // Reset form when dialog is closed
  const handleDialogChange = (open: boolean) => {
    if (!open) {
      setForm({
        title: "",
        description: "",
        date: "",
        start_time: "",
        duration: 30,
        event_type: defaultEventType,
        priority: defaultPriority,
        location: "",
        meeting_url: "",
        notes: "",
      });
    }
    onOpenChange(open);
  };

  return (
    <Dialog open={open} onOpenChange={handleDialogChange}>
      <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Create Event for Lead</DialogTitle>
          <DialogDescription>Schedule a new event for this lead. The lead will be added as an attendee.</DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Title *</label>
            <Input value={form.title} onChange={e => handleChange("title", e.target.value)} className="border-black" required />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
            <Textarea value={form.description} onChange={e => handleChange("description", e.target.value)} className="border-black" />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Date *</label>
              <Input type="date" value={form.date} onChange={e => handleChange("date", e.target.value)} className="border-black" required />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Start Time *</label>
              <Input type="time" value={form.start_time} onChange={e => handleChange("start_time", e.target.value)} className="border-black" required />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Duration (minutes)</label>
            <Input type="number" value={form.duration} onChange={e => handleChange("duration", parseInt(e.target.value))} className="border-black" min="1" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Event Type</label>
            <Select value={form.event_type} onValueChange={value => handleChange("event_type", value)}>
              <SelectTrigger className="border-black">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="meeting">Meeting</SelectItem>
                <SelectItem value="call">Call</SelectItem>
                <SelectItem value="demo">Demo</SelectItem>
                <SelectItem value="follow_up">Follow-up</SelectItem>
                <SelectItem value="presentation">Presentation</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Priority</label>
            <Select value={form.priority} onValueChange={value => handleChange("priority", value)}>
              <SelectTrigger className="border-black">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="low">Low</SelectItem>
                <SelectItem value="medium">Medium</SelectItem>
                <SelectItem value="high">High</SelectItem>
                <SelectItem value="urgent">Urgent</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Location</label>
            <Input value={form.location} onChange={e => handleChange("location", e.target.value)} className="border-black" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Meeting URL</label>
            <Input value={form.meeting_url} onChange={e => handleChange("meeting_url", e.target.value)} className="border-black" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Notes</label>
            <Textarea value={form.notes} onChange={e => handleChange("notes", e.target.value)} className="border-black" />
          </div>
          <div className="flex justify-end gap-3">
            <Button variant="outline" type="button" onClick={() => onOpenChange(false)} className="border-black text-black">Cancel</Button>
            <Button type="submit" className="bg-black text-white hover:bg-gray-800" disabled={isLoading}>
              {isLoading ? "Creating..." : "Create Event"}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
} 