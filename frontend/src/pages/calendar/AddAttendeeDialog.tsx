import { useState, useEffect } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";
import { toast } from "sonner";
import { leadApi } from "@/lib/leadApi";
import { calendarApi } from "@/lib/calendarApi";
import { authApi } from "@/lib/authApi";

export default function AddAttendeeDialog({ open, onOpenChange, eventId, onAttendeeAdded }: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  eventId: number;
  onAttendeeAdded: () => void;
}) {
  const [form, setForm] = useState({
    name: "",
    email: "",
    phone: "",
    company: "",
    job_title: "",
    lead_id: "",
    is_organizer: false,
    is_required: true,
    response_notes: ""
  });
  const [isLoading, setIsLoading] = useState(false);
  const [leads, setLeads] = useState<any[]>([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [filteredLeads, setFilteredLeads] = useState<any[]>([]);
  const [showLeadResults, setShowLeadResults] = useState(false);
  const userId = authApi.getUserId();
  useEffect(() => {
    if (!open) return;
    // Fetch all leads on open
    leadApi.getLeads().then(res => setLeads(res.leads || []));
  }, [open]);

  useEffect(() => {
    if (searchTerm.trim() === '') {
      setFilteredLeads([]);
      setShowLeadResults(false);
      return;
    }
    const searchTermLower = searchTerm.toLowerCase();
    const filtered = leads.filter(lead =>
      lead.full_name?.toLowerCase().includes(searchTermLower) ||
      lead.email?.toLowerCase().includes(searchTermLower) ||
      lead.company?.toLowerCase().includes(searchTermLower) ||
      lead.phone?.toLowerCase().includes(searchTermLower) ||
      lead.job_title?.toLowerCase().includes(searchTermLower)
    );
    setFilteredLeads(filtered);
    setShowLeadResults(true);
  }, [searchTerm, leads]);

  const handleLeadSelect = (lead: any) => {
    setForm({
      ...form,
      name: lead.full_name || "",
      email: lead.email || "",
      phone: lead.phone || "",
      company: lead.company || "",
      job_title: lead.job_title || "",
      lead_id: lead.id.toString(),
    });
    setSearchTerm(lead.full_name);
    setShowLeadResults(false);
  };

  const handleChange = (field: string, value: any) => {
    setForm(prev => ({ ...prev, [field]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.name || !form.email) {
      toast.error("Name and email are required");
      return;
    }
    setIsLoading(true);
    try {
      const api = calendarApi();
      await api.addAttendeeToEvent(eventId, {
        ...form,
        lead_id: form.lead_id ? parseInt(form.lead_id) : undefined,
        user_id: userId.toString()
      });
      toast.success("Attendee added successfully");
      onAttendeeAdded();
      setForm({
        name: "",
        email: "",
        phone: "",
        company: "",
        job_title: "",
        lead_id: "",
        is_organizer: false,
        is_required: true,
        response_notes: ""
      });
      setSearchTerm("");
    } catch (err) {
      toast.error("Failed to add attendee");
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDialogChange = (open: boolean) => {
    if (!open) {
      setForm({
        name: "",
        email: "",
        phone: "",
        company: "",
        job_title: "",
        lead_id: "",
        is_organizer: false,
        is_required: true,
        response_notes: ""
      });
      setSearchTerm("");
    }
    onOpenChange(open);
  };

  return (
    <Dialog open={open} onOpenChange={handleDialogChange}>
      <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Add Attendee</DialogTitle>
          <DialogDescription>Add a new attendee to this event. You can search for a lead or enter details manually.</DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Lead Search Bar */}
          <div className="relative">
            <Input
              type="text"
              value={searchTerm}
              onChange={e => setSearchTerm(e.target.value)}
              placeholder="Search leads by name, email, company..."
              className="border-black focus:ring-black pr-10"
            />
            {searchTerm && showLeadResults && filteredLeads.length > 0 && (
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
                        {[lead.job_title, lead.phone].filter(Boolean).join(' • ')}
                      </span>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
          {/* Attendee Fields */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Name *</label>
            <Input value={form.name} onChange={e => handleChange("name", e.target.value)} className="border-black" required />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Email *</label>
            <Input value={form.email} onChange={e => handleChange("email", e.target.value)} className="border-black" required />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Phone</label>
            <Input value={form.phone} onChange={e => handleChange("phone", e.target.value)} className="border-black" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Company</label>
            <Input value={form.company} onChange={e => handleChange("company", e.target.value)} className="border-black" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Job Title</label>
            <Input value={form.job_title} onChange={e => handleChange("job_title", e.target.value)} className="border-black" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Lead ID</label>
            <Input value={form.lead_id} onChange={e => handleChange("lead_id", e.target.value)} className="border-black" />
          </div>
          <div className="flex items-center space-x-2">
            <Checkbox id="is_organizer" checked={form.is_organizer} onCheckedChange={checked => handleChange("is_organizer", checked)} />
            <label htmlFor="is_organizer" className="text-black">Is Organizer</label>
          </div>
          <div className="flex items-center space-x-2">
            <Checkbox id="is_required" checked={form.is_required} onCheckedChange={checked => handleChange("is_required", checked)} />
            <label htmlFor="is_required" className="text-black">Required Attendee</label>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Response Notes</label>
            <Input value={form.response_notes} onChange={e => handleChange("response_notes", e.target.value)} className="border-black" />
          </div>
          <div className="flex justify-end gap-3">
            <Button variant="outline" type="button" onClick={() => onOpenChange(false)} className="border-black text-black">Cancel</Button>
            <Button type="submit" className="bg-black text-white hover:bg-gray-800" disabled={isLoading}>
              {isLoading ? "Adding..." : "Add Attendee"}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
} 