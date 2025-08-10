import { useState, useEffect } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ArrowLeft, Calendar, Clock, User, MapPin, Edit, Trash2, UserPlus, AlertTriangle } from "lucide-react";
import { Event, EventConflictsResponse, Attendee, calendarApi, Campaign, authApi } from "@/lib/api";
import { crmApi } from "@/lib/crmAPI";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import AddAttendeeDialog from "./AddAttendeeDialog";
import { toast } from "sonner";
import LeadEventCreateDialog from "./LeadEventCreateDialog";
import { Textarea } from "@/components/ui/textarea";
import { Skeleton } from "@/components/ui/skeleton";

const EventDetails = () => {
  const { eventId } = useParams<{ eventId: string }>();
  const navigate = useNavigate();
  const [event, setEvent] = useState<Event | null>(null);
  const [attendees, setAttendees] = useState<Attendee[]>([]);
  const [conflicts, setConflicts] = useState<EventConflictsResponse | null>(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [isEditLoading, setIsEditLoading] = useState(false);
  const [editForm, setEditForm] = useState<any>(null);
  const [editError, setEditError] = useState<string | null>(null);
  const [isAddAttendeeOpen, setIsAddAttendeeOpen] = useState(false);
  const [deletingAttendeeId, setDeletingAttendeeId] = useState<number | null>(null);
  const [showDeleteAttendeeConfirm, setShowDeleteAttendeeConfirm] = useState(false);
  const [attendeeToDelete, setAttendeeToDelete] = useState<Attendee | null>(null);
  const [isAddToCampaignOpen, setIsAddToCampaignOpen] = useState(false);
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [selectedCampaign, setSelectedCampaign] = useState<Campaign | null>(null);
  const [isCampaignLoading, setIsCampaignLoading] = useState(false);
  const [campaignError, setCampaignError] = useState<string | null>(null);
  const [isCreateFollowUpOpen, setIsCreateFollowUpOpen] = useState(false);

  // Initialize APIs
  const api = calendarApi();

  // Fetch event details and conflicts on mount
  useEffect(() => {
    const fetchEventData = async () => {
      if (!eventId) {
        setError("Invalid event ID");
        setIsLoading(false);
        return;
      }

      setIsLoading(true);
      setError(null);

      try {
        // Fetch event details with attendees and lead info
        const eventResponse = await api.getEventById(Number(eventId), {
          include_attendees: true,
          include_lead_info: true,
        });
        setEvent(eventResponse);
        setAttendees(eventResponse.attendees || []);

        // Fetch conflicts
        const conflictsResponse = await api.checkEventConflicts(Number(eventId));
        setConflicts(conflictsResponse);
      } catch (err) {
        setError("Failed to fetch event details or conflicts");
        console.error(err);
        toast.error("Failed to fetch event details or conflicts");
      } finally {
        setIsLoading(false);
      }
    };

    fetchEventData();
  }, [eventId]);

  // Fetch campaigns when dialog opens
  useEffect(() => {
    const fetchCampaigns = async () => {
      if (!isAddToCampaignOpen) {
        setCampaigns([]);
        return;
      }

      setIsCampaignLoading(true);
      setCampaignError(null);
      try {
        const userId = await authApi.getUserId();
        const response = await crmApi.getCampaigns(userId);
        setCampaigns(response as Campaign[]);
      } catch (err) {
        setCampaignError("Failed to fetch campaigns");
        console.error(err);
        toast.error("Failed to fetch campaigns");
      } finally {
        setIsCampaignLoading(false);
      }
    };

    fetchCampaigns();
  }, [isAddToCampaignOpen]);

  // Get unique lead IDs from event and attendees
  const getAssociatedLeads = (): { id: number; name: string; email: string; company?: string; job_title?: string }[] => {
    const leadIds = new Set<number>();
    const leads: { id: number; name: string; email: string; company?: string; job_title?: string }[] = [];

    // Add event's lead
    if (event?.lead_id && event.lead_info) {
      leadIds.add(event.lead_id);
      leads.push({
        id: event.lead_id,
        name: event.lead_info.full_name || event.lead_name || "Unknown",
        email: event.lead_info.email || event.lead_email || "",
        company: event.lead_info.company || event.lead_company,
        job_title: event.lead_info.job_title,
      });
    }

    // Add attendees' leads
    attendees.forEach((attendee) => {
      if (attendee.lead_id && !leadIds.has(attendee.lead_id)) {
        leadIds.add(attendee.lead_id);
        leads.push({
          id: attendee.lead_id,
          name: attendee.lead_info?.full_name || attendee.name,
          email: attendee.lead_info?.email || attendee.email,
          company: attendee.lead_info?.company || attendee.company,
          job_title: attendee.lead_info?.job_title || attendee.job_title,
        });
      }
    });

    return leads;
  };

  const associatedLeads = getAssociatedLeads();

  const handleAddToCampaign = async () => {
    if (!selectedCampaign || associatedLeads.length === 0) {
      toast.error("Please select a campaign and ensure there are leads to add");
      return;
    }

    setIsCampaignLoading(true);
    setCampaignError(null);
    try {
      const leadIds = associatedLeads.map((lead) => lead.id);
      const userId = await authApi.getUserId();
      await crmApi.addBulkLeadsToCampaign(userId, selectedCampaign.id, { lead_ids: leadIds });
      toast.success(`Successfully added ${leadIds.length} lead(s) to campaign "${selectedCampaign.name}"`);
      setIsAddToCampaignOpen(false);
      setSelectedCampaign(null);
      setCampaigns([]);
    } catch (err) {
      setCampaignError("Failed to add leads to campaign");
      console.error(err);
      toast.error("Failed to add leads to campaign");
    } finally {
      setIsCampaignLoading(false);
    }
  };

  const handleDeleteEvent = async () => {
    if (!eventId) return;

    try {
      await api.deleteEvent(Number(eventId));
      setShowDeleteConfirm(false);
      navigate("/calendar");
      toast.success("Event deleted successfully");
    } catch (err) {
      setError("Failed to delete event");
      console.error(err);
      toast.error("Failed to delete event");
    }
  };

  const getEventTypeColor = (type: string) => {
    switch (type) {
      case "meeting": return "bg-blue-50 text-blue-700 border-blue-200";
      case "call": return "bg-green-50 text-green-700 border-green-200";
      case "demo": return "bg-purple-50 text-purple-700 border-purple-200";
      case "follow_up": return "bg-orange-50 text-orange-700 border-orange-200";
      default: return "bg-gray-50 text-gray-700 border-gray-200";
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case "urgent": return "bg-red-50 text-red-700 border-red-200";
      case "high": return "bg-orange-50 text-orange-700 border-orange-200";
      case "medium": return "bg-yellow-50 text-yellow-700 border-yellow-200";
      case "low": return "bg-gray-50 text-gray-700 border-gray-200";
      default: return "bg-gray-50 text-gray-700 border-gray-200";
    }
  };

  const getStatusColor = (status: string | undefined) => {
    switch (status) {
      case "accepted": return "bg-green-50 text-green-700 border-green-200";
      case "declined": return "bg-red-50 text-red-700 border-red-200";
      case "tentative": return "bg-yellow-50 text-yellow-700 border-yellow-200";
      case "no_response": return "bg-gray-50 text-gray-700 border-gray-200";
      default: return "bg-gray-50 text-gray-700 border-gray-200";
    }
  };

  // Format duration from duration_minutes
  const formatDuration = (minutes: number) => {
    if (minutes >= 60) {
      const hours = Math.floor(minutes / 60);
      const remainingMinutes = minutes % 60;
      return `${hours} hour${hours > 1 ? "s" : ""}${remainingMinutes > 0 ? ` ${remainingMinutes} minutes` : ""}`;
    }
    return `${minutes} minutes`;
  };

  // Parse tags string into an array
  const parseTags = (tags: string | undefined): string[] => {
    return tags ? tags.split(",").map(tag => tag.trim()) : [];
  };

  const handleOpenEditModal = async () => {
    if (!eventId) return;
    setIsEditModalOpen(true);
    setIsEditLoading(true);
    setEditError(null);
    try {
      const apiEvent = await api.getEventById(Number(eventId), { include_attendees: true, include_lead_info: true });
      setEditForm({
        title: apiEvent.title || "",
        description: apiEvent.description || "",
        date: apiEvent.start_datetime ? apiEvent.start_datetime.slice(0, 10) : "",
        start_time: apiEvent.start_datetime ? new Date(apiEvent.start_datetime).toISOString().slice(11, 16) : "",
        duration: apiEvent.duration_minutes || 0,
        priority: apiEvent.priority || "low",
        notes: apiEvent.notes || "",
        location: apiEvent.location || "",
        meeting_url: apiEvent.meeting_url || "",
      });
    } catch (err) {
      setEditError("Failed to fetch event details");
      setEditForm(null);
      console.error(err);
      toast.error("Failed to fetch event details");
    } finally {
      setIsEditLoading(false);
    }
  };

  const saveEditEvent = async () => {
    if (!editForm) return;
    try {
      const updateData: any = {
        title: editForm.title,
        priority: editForm.priority,
        notes: editForm.notes,
        location: editForm.location,
        description: editForm.description,
        meeting_url: editForm.meeting_url,
      };
      if (editForm.date && editForm.start_time) {
        const startDateTime = new Date(`${editForm.date}T${editForm.start_time}`);
        if (isNaN(startDateTime.getTime())) throw new Error("Invalid start date/time");
        updateData.start_datetime = startDateTime.toISOString();
        if (editForm.duration) {
          const endDateTime = new Date(startDateTime.getTime() + (editForm.duration * 60000));
          updateData.end_datetime = endDateTime.toISOString();
        }
      }
      await api.updateEvent(Number(eventId), updateData);
      // Update local event state
      setEvent((prev) => prev ? { ...prev, ...updateData } : prev);
      setIsEditModalOpen(false);
      setEditForm(null);
      toast.success("Event updated successfully");
    } catch (err) {
      setEditError(err instanceof Error ? err.message : "Failed to update event");
      console.error(err);
      toast.error("Failed to update event");
    }
  };

  const handleDeleteAttendee = async (attendee: Attendee) => {
    setAttendeeToDelete(attendee);
    setShowDeleteAttendeeConfirm(true);
  };

  const confirmDeleteAttendee = async () => {
    if (!attendeeToDelete) return;
    setDeletingAttendeeId(attendeeToDelete.id);
    try {
      await api.deleteAttendee(attendeeToDelete.id);
      // Refresh attendees
      if (eventId) {
        const eventResponse = await api.getEventById(Number(eventId), { include_attendees: true, include_lead_info: true });
        setAttendees(eventResponse.attendees || []);
        toast.success("Attendee deleted successfully");
      }
    } catch (err) {
      console.error(err);
      toast.error("Failed to delete attendee");
    } finally {
      setDeletingAttendeeId(null);
      setShowDeleteAttendeeConfirm(false);
      setAttendeeToDelete(null);
    }
  };

  return (
    <div className="min-h-screen  p-4 lg:p-8">
      <div className="max-w-6xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4">
          <Link to="/calendar">
            <Button variant="outline" size="sm" className=" text-black hover:bg-gray-50">
              <ArrowLeft className="w-4 h-4 " />
              {/* Back to Calendar */}
            </Button>
          </Link>
          <div className="flex-1">
            <h1 className="text-2xl lg:text-3xl font-bold text-black flex items-center">
              <Calendar className="w-8 h-8 mr-3" />
              Event Details
            </h1>
            <p className="text-gray-600 mt-1">View and manage event information</p>
          </div>
          {event && (
            <div className="flex flex-col sm:flex-row gap-2">
              <Link to="#" onClick={handleOpenEditModal}>
                <Button variant="outline" className=" text-black hover:bg-gray-50">
                  <Edit className="w-4 h-4 mr-2" />
                  Edit Event
                </Button>
              </Link>
              <Button
                variant="outline"
                onClick={() => setShowDeleteConfirm(true)}
                className="border-red-300 text-red-700 hover:bg-red-50"
              >
                <Trash2 className="w-4 h-4 mr-2" />
                Delete
              </Button>
            </div>
          )}
        </div>

        {isLoading ? (
          <Card className=" ">
            <CardContent className="p-6">
              <div className="space-y-6">
                <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4 mb-6">
                  <Skeleton className="h-10 w-32 mb-4" />
                  <div className="flex-1">
                    <Skeleton className="h-8 w-48 mb-2" />
                    <Skeleton className="h-4 w-64" />
                  </div>
                  <Skeleton className="h-10 w-40" />
                </div>
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                  <div className="lg:col-span-2 space-y-6">
                    <Skeleton className="h-40 w-full mb-4" />
                    <Skeleton className="h-40 w-full mb-4" />
                  </div>
                  <div className="space-y-6">
                    <Skeleton className="h-40 w-full mb-4" />
                    <Skeleton className="h-40 w-full mb-4" />
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        ) : error ? (
          <Card className="border-red-300 bg-red-50">
            <CardContent className="p-6 text-center">
              <p className="text-red-700">{error}</p>
            </CardContent>
          </Card>
        ) : !event ? (
          <Card className=" ">
            <CardContent className="p-6 text-center">
              <p className="text-gray-500">Event not found</p>
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Event Information */}
            <div className="lg:col-span-2 space-y-6">
              <Card className=" ">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-black">{event.title}</CardTitle>
                    <div className="flex gap-2">
                      <Badge className={getEventTypeColor(event.event_type)}>
                        {event.event_type}
                      </Badge>
                      <Badge className={getPriorityColor(event.priority)}>
                        {event.priority}
                      </Badge>
                      {event.is_recurring && (
                        <Badge className="bg-indigo-50 text-indigo-700 border-indigo-200">
                          Recurring
                        </Badge>
                      )}
                      {event.is_past && (
                        <Badge className="bg-gray-50 text-gray-700 border-gray-200">
                          Past
                        </Badge>
                      )}
                      {event.is_upcoming && (
                        <Badge className="bg-green-50 text-green-700 border-green-200">
                          Upcoming
                        </Badge>
                      )}
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="space-y-4">
                      <div className="flex items-center gap-3">
                        <Clock className="w-5 h-5 text-gray-600" />
                        <div>
                          <div className="font-medium text-black">
                            {event.all_day ? "All Day" : `${event.start_datetime.split('T')[1]} ${event.start_datetime.split('T')[0]}`}
                          </div>
                          {!event.all_day && (
                            <div className="text-sm text-gray-600">
                              {formatDuration(event.duration_minutes || 0)}
                            </div>
                          )}
                        </div>
                      </div>
                      <div className="flex items-center gap-3">
                        <MapPin className="w-5 h-5 text-gray-600" />
                        <div>
                          <div className="font-medium text-black">{event.location || "N/A"}</div>
                          {event.meeting_url && (
                            <a
                              href={event.meeting_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-sm text-blue-600 hover:underline"
                            >
                              Join Meeting
                            </a>
                          )}
                        </div>
                      </div>
                      <div className="flex items-center gap-3">
                        <User className="w-5 h-5 text-gray-600" />
                        <div>
                          <div className="font-medium text-black">{event.lead_info?.full_name || event.lead_name || "N/A"}</div>
                          <div className="text-sm text-gray-600">{event.lead_info?.company || event.lead_company || "N/A"}</div>
                          {event.lead_email && (
                            <div className="text-sm text-gray-600">
                              <a href={`mailto:${event.lead_email}`} className="hover:underline">{event.lead_email}</a>
                            </div>
                          )}
                          {event.lead_phone && (
                            <div className="text-sm text-gray-600">
                              <a href={`tel:${event.lead_phone}`} className="hover:underline">{event.lead_phone}</a>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                    <div className="space-y-4">
                      {event.deal_value && (
                        <div>
                          <div className="text-sm font-medium text-gray-600">Deal Value</div>
                          <div className="text-lg font-bold text-black">${event.deal_value.toLocaleString()}</div>
                        </div>
                      )}
                      {event.deal_stage && (
                        <div>
                          <div className="text-sm font-medium text-gray-600">Deal Stage</div>
                          <Badge className="bg-blue-50 text-blue-700 border-blue-200">
                            {event.deal_stage}
                          </Badge>
                        </div>
                      )}
                      {event.reminder_minutes && event.reminder_minutes.length > 0 && (
                        <div>
                          <div className="text-sm font-medium text-gray-600">Reminders</div>
                          <div className="text-sm text-black">
                            {event.reminder_minutes.join(", ")} minutes before
                            {event.email_reminders && " (Email)"}
                            {event.sms_reminders && " (SMS)"}
                          </div>
                        </div>
                      )}
                      {event.tags && (
                        <div>
                          <div className="text-sm font-medium text-gray-600">Tags</div>
                          <div className="flex flex-wrap gap-1 mt-1">
                            {parseTags(event.tags).map((tag, index) => (
                              <Badge key={index} variant="outline" className=" text-black">
                                {tag}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>

                  {event.description && (
                    <div>
                      <div className="text-sm font-medium text-gray-600 mb-2">Description</div>
                      <p className="text-black">{event.description}</p>
                    </div>
                  )}

                  {event.notes && (
                    <div>
                      <div className="text-sm font-medium text-gray-600 mb-2">Notes</div>
                      <p className="text-black">{event.notes}</p>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Attendees */}
              <Card className=" ">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-black flex items-center">
                      <User className="w-5 h-5 mr-2" />
                      Attendees ({attendees.length})
                    </CardTitle>
                    <Button variant="outline" className=" text-black hover:bg-gray-50" onClick={() => setIsAddAttendeeOpen(true)}>
                      <UserPlus className="w-4 h-4 mr-2" />
                      Add Attendee
                    </Button>
                  </div>
                </CardHeader>
                <CardContent>
                  {attendees.length > 0 ? (
                    <div className="space-y-3">
                      {attendees.map((attendee) => (
                        <div key={attendee.id} className="flex items-center justify-between p-3  border-gray-200 rounded-lg">
                          <div className="flex-1">
                            <div className="flex items-center gap-2">
                              <div className="font-medium text-black">{attendee.name}</div>
                              {attendee.is_organizer && (
                                <Badge variant="outline" className="border-blue-300 text-blue-700">
                                  Organizer
                                </Badge>
                              )}
                              {attendee.is_required && (
                                <Badge variant="outline" className="border-orange-300 text-orange-700">
                                  Required
                                </Badge>
                              )}
                            </div>
                            <div className="text-sm text-gray-600">
                              <a href={`mailto:${attendee.email}`} className="hover:underline">{attendee.email}</a>
                            </div>
                            <div className="text-sm text-gray-600">{attendee.company || "N/A"}</div>
                            {attendee.job_title && (
                              <div className="text-sm text-gray-600">{attendee.job_title}</div>
                            )}
                            {attendee.response_notes && (
                              <div className="text-sm text-gray-600">Note: {attendee.response_notes}</div>
                            )}
                          </div>
                          <Badge className={getStatusColor(attendee.status)}>
                            {attendee.status || "No response"}
                          </Badge>
                          <Button
                            variant="ghost"
                            size="icon"
                            className="ml-2 text-red-600 hover:bg-red-50"
                            onClick={() => handleDeleteAttendee(attendee)}
                            disabled={deletingAttendeeId === attendee.id}
                            title="Delete Attendee"
                          >
                            <Trash2 className="w-5 h-5" />
                          </Button>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-gray-500 text-center py-4">No attendees found</p>
                  )}
                </CardContent>
              </Card>
            </div>

            {/* Sidebar */}
            <div className="space-y-6">
              {/* Quick Actions */}
              <Card className=" ">
                <CardHeader>
                  <CardTitle className="text-black">Quick Actions</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  {event.lead_id && (
                    <Link to={`/calendar/leads/${event.lead_id}`}>
                      <Button variant="outline" className="w-full  text-black hover:bg-gray-50">
                        View Lead Events
                      </Button>
                    </Link>
                  )}
                  <Button
                    variant="outline"
                    className="w-full  text-black hover:bg-gray-50"
                    onClick={() => setIsAddToCampaignOpen(true)}
                  >
                    Add to Outreach Campaign
                  </Button>
                  <Button
                    variant="outline"
                    className="w-full  text-black hover:bg-gray-50"
                    onClick={() => setIsCreateFollowUpOpen(true)}
                  >
                    Schedule Follow-up
                  </Button>
                </CardContent>
              </Card>

              {/* Conflicts */}
              {conflicts && conflicts.has_conflicts && (
                <Card className="border-red-300 bg-red-50">
                  <CardHeader>
                    <CardTitle className="text-red-700 flex items-center">
                      <AlertTriangle className="w-5 h-5 mr-2" />
                      Schedule Conflicts ({conflicts.conflict_count})
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      {conflicts.conflicts.map((conflict) => (
                        <div key={conflict.id} className="  border-red-200 rounded p-3">
                          <div className="font-medium text-red-700">{conflict.title}</div>
                          <div className="text-sm text-red-600">
                            {conflict.start_datetime} - {conflict.end_datetime}
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          </div>
        )}

        {/* Delete Confirmation Modal */}
        <Dialog open={showDeleteConfirm} onOpenChange={setShowDeleteConfirm}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle className="text-red-700">Delete Event</DialogTitle>
              <DialogDescription>
                Are you sure you want to delete "{event?.title}"? This action cannot be undone.
              </DialogDescription>
            </DialogHeader>
            <div className="flex gap-3 justify-end">
              <Button
                variant="outline"
                onClick={() => setShowDeleteConfirm(false)}
                className=" text-black hover:bg-gray-50"
              >
                Cancel
              </Button>
              <Button
                onClick={handleDeleteEvent}
                className="bg-red-600 text-white hover:bg-red-700"
              >
                Delete Event
              </Button>
            </div>
          </DialogContent>
        </Dialog>

        {/* Edit Event Modal */}
        <Dialog open={isEditModalOpen} onOpenChange={setIsEditModalOpen}>
          <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>Edit Event</DialogTitle>
              <DialogDescription>
                Make changes to your event here. Click save when you're done.
              </DialogDescription>
            </DialogHeader>
            {isEditLoading ? (
              <div className="py-8 text-center text-gray-500">Loading event details...</div>
            ) : editError && !editForm ? (
              <div className="py-8 text-center text-red-500">{editError}</div>
            ) : editForm && (
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Title</label>
                  <Input
                    value={editForm.title}
                    onChange={(e) => setEditForm({ ...editForm, title: e.target.value })}
                    className=""
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                  <Textarea
                    value={editForm.description || ""}
                    onChange={(e) => setEditForm({ ...editForm, description: e.target.value })}
                    className="w-full min-h-[60px] p-2 rounded-md"
                    placeholder="Add event description..."
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Date</label>
                    <Input
                      type="date"
                      value={editForm.date}
                      onChange={(e) => setEditForm({ ...editForm, date: e.target.value })}
                      className=""
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Start Time</label>
                    <Input
                      type="time"
                      value={editForm.start_time}
                      onChange={(e) => setEditForm({ ...editForm, start_time: e.target.value })}
                      className=""
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Duration (minutes)</label>
                  <Input
                    type="number"
                    value={editForm.duration}
                    onChange={(e) => setEditForm({ ...editForm, duration: parseInt(e.target.value) })}
                    className=""
                    min="1"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Priority</label>
                  <Select value={editForm.priority} onValueChange={(value) => setEditForm({ ...editForm, priority: value })}>
                    <SelectTrigger className="">
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
                  <label className="block text-sm font-medium text-gray-700 mb-1">Notes</label>
                  <Textarea
                    value={editForm.notes || ""}
                    onChange={(e) => setEditForm({ ...editForm, notes: e.target.value })}
                    className="w-full min-h-[100px] p-2 border  rounded-md"
                    placeholder="Add event notes..."
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Location</label>
                  <Input
                    value={editForm.location || ""}
                    onChange={(e) => setEditForm({ ...editForm, location: e.target.value })}
                    className=""
                    placeholder="Enter location"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Meeting URL</label>
                  <Input
                    value={editForm.meeting_url || ""}
                    onChange={(e) => setEditForm({ ...editForm, meeting_url: e.target.value })}
                    className=""
                    placeholder="Enter meeting URL"
                  />
                </div>
                <div className="flex justify-end gap-3">
                  <Button variant="outline" onClick={() => setIsEditModalOpen(false)} className=" text-black">
                    Cancel
                  </Button>
                  <Button onClick={saveEditEvent} className="bg-black text-white hover:bg-gray-800">
                    Save Changes
                  </Button>
                </div>
              </div>
            )}
          </DialogContent>
        </Dialog>

        {/* Add to Campaign Dialog */}
        <Dialog open={isAddToCampaignOpen} onOpenChange={(open) => {
          setIsAddToCampaignOpen(open);
          if (!open) {
            setCampaigns([]);
            setSelectedCampaign(null);
            setCampaignError(null);
          }
        }}>
          <DialogContent className="max-w-3xl max-h-[80vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>Add Leads to Campaign</DialogTitle>
              <DialogDescription>
                Select a campaign to add associated leads to it.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-6">
              {/* Campaign Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Select Campaign</label>
                <Select
                  value={selectedCampaign?.id.toString() || ""}
                  onValueChange={(value) => {
                    const campaign = campaigns.find((c) => c.id.toString() === value);
                    setSelectedCampaign(campaign || null);
                  }}
                  disabled={isCampaignLoading || campaigns.length === 0}
                >
                  <SelectTrigger className="">
                    <SelectValue placeholder={isCampaignLoading ? "Loading..." : "Select a campaign"} />
                  </SelectTrigger>
                  <SelectContent>
                    {campaigns.map((campaign) => (
                      <SelectItem key={campaign.id} value={campaign.id.toString()}>
                        {campaign.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {isCampaignLoading && (
                  <div className="mt-2 text-center text-gray-500">Loading campaigns...</div>
                )}
                {campaignError && (
                  <div className="mt-2 text-center text-red-500">{campaignError}</div>
                )}
                {!isCampaignLoading && campaigns.length === 0 && !campaignError && (
                  <div className="mt-2 text-center text-gray-500">No campaigns available</div>
                )}
                {selectedCampaign && (
                  <div className="mt-2 p-2 bg-gray-50 rounded-md">
                    <div className="text-sm font-medium">Selected Campaign: {selectedCampaign.name}</div>
                    <div className="text-xs text-gray-500">{selectedCampaign.description || "No description"}</div>
                  </div>
                )}
              </div>

              {/* Associated Leads */}
              <div>
                <h3 className="text-lg font-semibold text-black flex items-center">
                  <User className="w-5 h-5 mr-2" />
                  Associated Leads ({associatedLeads.length})
                </h3>
                {associatedLeads.length > 0 ? (
                  <div className="mt-4 space-y-3">
                    {associatedLeads.map((lead) => (
                      <div key={lead.id} className="p-3  border-gray-200 rounded-lg">
                        <div className="font-medium text-black">{lead.name}</div>
                        <div className="text-sm text-gray-600">
                          <a href={`mailto:${lead.email}`} className="hover:underline">{lead.email}</a>
                        </div>
                        <div className="text-sm text-gray-600">{lead.company || "N/A"}</div>
                        {lead.job_title && (
                          <div className="text-sm text-gray-600">{lead.job_title}</div>
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="mt-4 text-gray-500 text-center">No leads associated with this event</p>
                )}
              </div>

              {/* Action Buttons */}
              <div className="flex justify-end gap-3">
                <Button
                  variant="outline"
                  onClick={() => setIsAddToCampaignOpen(false)}
                  className=" text-black"
                >
                  Cancel
                </Button>
                <Button
                  onClick={handleAddToCampaign}
                  className="bg-black text-white hover:bg-gray-800"
                  disabled={isCampaignLoading || !selectedCampaign || associatedLeads.length === 0}
                >
                  Add to Campaign
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>

        {/* Add Attendee Dialog */}
        <AddAttendeeDialog
          open={isAddAttendeeOpen}
          onOpenChange={setIsAddAttendeeOpen}
          eventId={event ? event.id : 0}
          onAttendeeAdded={async () => {
            setIsAddAttendeeOpen(false);
            if (eventId) {
              const eventResponse = await api.getEventById(Number(eventId), { include_attendees: true, include_lead_info: true });
              setAttendees(eventResponse.attendees || []);
              toast.success("Attendee added successfully");
            }
          }}
        />

        {/* Delete Attendee Confirmation Modal */}
        <Dialog open={showDeleteAttendeeConfirm} onOpenChange={setShowDeleteAttendeeConfirm}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle className="text-red-700">Delete Attendee</DialogTitle>
              <DialogDescription>
                Are you sure you want to delete attendee "{attendeeToDelete?.name}"? This action cannot be undone.
              </DialogDescription>
            </DialogHeader>
            <div className="flex gap-3 justify-end">
              <Button
                variant="outline"
                onClick={() => setShowDeleteAttendeeConfirm(false)}
                className=" text-black hover:bg-gray-50"
              >
                Cancel
              </Button>
              <Button
                onClick={confirmDeleteAttendee}
                className="bg-red-600 text-white hover:bg-red-700"
                disabled={deletingAttendeeId === attendeeToDelete?.id}
              >
                Delete Attendee
              </Button>
            </div>
          </DialogContent>
        </Dialog>

        {/* Schedule Follow-up Dialog */}
        <LeadEventCreateDialog
          open={isCreateFollowUpOpen}
          onOpenChange={setIsCreateFollowUpOpen}
          lead={event?.lead_info || null}
          onEventCreated={() => {
            setIsCreateFollowUpOpen(false);
            toast.success("Follow-up event created successfully");
            // Optionally, refresh event details here
          }}
        />
      </div>
    </div>
  );
};

export default EventDetails;