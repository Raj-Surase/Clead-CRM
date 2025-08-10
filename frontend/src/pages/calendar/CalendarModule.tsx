import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Calendar } from "@/components/ui/calendar";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogDescription } from "@/components/ui/dialog";
import { CalendarIcon, Plus, Search, Clock, User, MapPin, Edit, Trash2, Loader2, X } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import { CalendarSummaryResponse, CalendarSummaryEvent, calendarApi, Event as ApiEvent } from "@/lib/api";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";
import { leadApi } from "@/lib/leadApi";
import { Textarea } from "@/components/ui/textarea";
import { Skeleton } from "@/components/ui/skeleton";

// Extended interface for local use
interface ExtendedCalendarSummaryEvent extends CalendarSummaryEvent {
  description?: string;
  timezone?: string;
  all_day?: boolean;
  meeting_url?: string;
  meeting_id?: string;
  meeting_password?: string;
  deal_value?: number;
  deal_stage?: string;
  deal_probability?: number;
  notes?: string;
  tags?: string;
  custom_fields?: Record<string, any>;
  reminder_minutes?: number[];
  email_reminders?: boolean;
  sms_reminders?: boolean;
}

// Event update interface matching backend schema
interface EventUpdateData {
  title?: string;
  description?: string;
  start_datetime?: string;
  end_datetime?: string;
  timezone?: string;
  all_day?: boolean;
  event_type?: string;
  status?: string;
  priority?: string;
  location?: string;
  meeting_url?: string;
  meeting_id?: string;
  meeting_password?: string;
  deal_value?: number;
  deal_stage?: string;
  deal_probability?: number;
  notes?: string;
  tags?: string;
  custom_fields?: Record<string, any>;
  reminder_minutes?: number[];
  email_reminders?: boolean;
  sms_reminders?: boolean;
  user_id: string;
}

const CalendarModule = () => {
  const [selectedDate, setSelectedDate] = useState<Date | undefined>(new Date());
  // const [searchQuery, setSearchQuery] = useState("");
  const [selectedEvent, setSelectedEvent] = useState<ExtendedCalendarSummaryEvent | null>(null);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [calendarSummary, setCalendarSummary] = useState<CalendarSummaryResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isEditLoading, setIsEditLoading] = useState(false);
  const [isCreateEventDialogOpen, setIsCreateEventDialogOpen] = useState(false);
  const [isAvailabilityDialogOpen, setIsAvailabilityDialogOpen] = useState(false);
  const [leads, setLeads] = useState<any[]>([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [filteredLeads, setFilteredLeads] = useState<any[]>([]);
  const [showLeadResults, setShowLeadResults] = useState(false);
  const [availabilityData, setAvailabilityData] = useState<any | null>(null);
  const [showAvailabilityResults, setShowAvailabilityResults] = useState(false);
  const [searchUpcoming, setSearchUpcoming] = useState("");

  // Create Event Form State
  const [createEventForm, setCreateEventForm] = useState({
    title: "",
    description: "",
    start_datetime: "",
    end_datetime: "",
    event_type: "",
    priority: "",
    location: "",
    meeting_url: "",
    lead_id: "",
    lead_name: "",
    lead_email: "",
    lead_phone: "",
    lead_company: "",
    notes: "",
    reminder_minutes: [15],
    email_reminders: true,
    sms_reminders: false
  });

  // Availability Check Form State
  const [availabilityForm, setAvailabilityForm] = useState({
    start_date: "",
    end_date: "",
    duration_minutes: 30,
    timezone: "",
    buffer_minutes: 15
  });

  // Initialize calendar API
  const api = calendarApi();
  const navigate = useNavigate();

  // Fetch calendar summary on mount
  useEffect(() => {
    const fetchCalendarSummary = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const response = await api.getCalendarSummary(); // Fetch all events
        setCalendarSummary(response as CalendarSummaryResponse);
      } catch (err) {
        setError("Failed to fetch calendar summary");
        console.error(err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchCalendarSummary();
  }, []);

  // Add after the existing useEffect blocks
  useEffect(() => {
    // Fetch leads when component mounts
    const fetchLeads = async () => {
      try {
        const response = await leadApi.getLeads();
        setLeads(response.leads);
      } catch (error) {
        console.error('Error fetching leads:', error);
        toast.error('Failed to fetch leads');
      }
    };
    fetchLeads();
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
        lead.phone?.toLowerCase().includes(searchTermLower)
      );
    });
    setFilteredLeads(filtered);
    setShowLeadResults(true);
  }, [searchTerm, leads]);

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

  const getCalendarEventColor = (type: string) => {
    switch (type) {
      case "meeting": return "bg-blue-500";
      case "call": return "bg-green-500";
      case "demo": return "bg-purple-500";
      case "follow_up": return "bg-orange-500";
      default: return "bg-gray-500";
    }
  };

  // Remove the restriction on displaying events
  const allEvents = calendarSummary?.events_by_day
    ? Object.values(calendarSummary.events_by_day).flat().map(event => ({
        ...event,
        description: "",
        notes: "",
        meeting_url: "",
      }))
    : [];

  // Tab state for Upcoming Events
  const [upcomingTab, setUpcomingTab] = useState('all');

  // Tab filter logic
  const now = new Date();
  const startOfWeek = new Date(now);
  startOfWeek.setDate(now.getDate() - now.getDay());
  const endOfWeek = new Date(startOfWeek);
  endOfWeek.setDate(startOfWeek.getDate() + 6);
  const startOfMonth = new Date(now.getFullYear(), now.getMonth(), 1);
  const endOfMonth = new Date(now.getFullYear(), now.getMonth() + 1, 0);
  const startOfYear = new Date(now.getFullYear(), 0, 1);
  const endOfYear = new Date(now.getFullYear(), 11, 31);

  const filteredUpcomingEvents = allEvents.filter(event => {
    const eventDate = new Date(event.date);
    switch (upcomingTab) {
      case 'recent':
        const sevenDaysAgo = new Date(now);
        sevenDaysAgo.setDate(now.getDate() - 7);
        return eventDate >= sevenDaysAgo && eventDate <= now;
      case 'this_week':
        return eventDate >= startOfWeek && eventDate <= endOfWeek;
      case 'this_month':
        return eventDate >= startOfMonth && eventDate <= endOfMonth;
      case 'this_year':
        return eventDate >= startOfYear && eventDate <= endOfYear;
      default:
        return true;
    }
  });

  // Filtered upcoming events based on search
  const filteredUpcomingEventsBySearch = allEvents.filter(event => {
    if (!searchUpcoming.trim()) return true;
    const search = searchUpcoming.toLowerCase();
    return (
      event.title?.toLowerCase().includes(search) ||
      event.lead_name?.toLowerCase().includes(search) ||
      event.location?.toLowerCase().includes(search)
    );
  });

  // Utility to get local date string in YYYY-MM-DD
  function getLocalDateString(date: Date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  }

  const getEventsForDate = (date: Date) => {
    if (!calendarSummary?.events_by_day) return [];
    const dateKey = getLocalDateString(date);
    return calendarSummary.events_by_day[dateKey] || [];
  };

  const handleDateSelect = (date: Date | undefined) => {
    setSelectedDate(date);
  };

  const handleDeleteEvent = (event: ExtendedCalendarSummaryEvent) => {
    setSelectedEvent(event);
    setIsDeleteModalOpen(true);
  };

  const confirmDeleteEvent = async () => {
    if (selectedEvent) {
      try {
        await api.deleteEvent(selectedEvent.id);
        const refreshedSummary = await api.getCalendarSummary();
        setCalendarSummary(refreshedSummary as CalendarSummaryResponse);
      } catch (err) {
        setError("Failed to delete event");
        console.error(err);
      }
    }
    setIsDeleteModalOpen(false);
    setSelectedEvent(null);
  };


  const eventsOnSelectedDate = selectedDate ? getEventsForDate(selectedDate) : [];

  const handleCreateEventSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      const api = calendarApi();
      const eventData = {
        ...createEventForm,
        ...(createEventForm.lead_id && {
          lead_id: parseInt(createEventForm.lead_id),
        }),
      };

      await api.createEvent(eventData);
      toast.success('Event created successfully');
      setIsCreateEventDialogOpen(false);
      // Refresh calendar data (fetch all events)
      const refreshedSummary = await api.getCalendarSummary();
      setCalendarSummary(refreshedSummary as CalendarSummaryResponse);
    } catch (error) {
      console.error('Error creating event:', error);
      toast.error('Failed to create event');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCheckAvailability = async () => {
    if (!availabilityForm.start_date || !availabilityForm.end_date) {
      toast.error('Please select both start and end dates');
      return;
    }

    setIsLoading(true);
    try {
      const api = calendarApi();
      const endDate = new Date(availabilityForm.end_date);
      endDate.setDate(endDate.getDate() + 1);

      const response = await api.checkAvailability({
        start_date: `${availabilityForm.start_date}T00:00:00Z`,
        end_date: `${endDate.toISOString().split('T')[0]}T00:00:00Z`,
        duration_minutes: availabilityForm.duration_minutes,
        timezone: availabilityForm.timezone,
        buffer_minutes: availabilityForm.buffer_minutes,
      });
      setAvailabilityData(response);
      setShowAvailabilityResults(true);
    } catch (error) {
      console.error('Error checking availability:', error);
      toast.error('Failed to check availability');
    } finally {
      setIsLoading(false);
    }
  };

  const formatTime = (dateTimeString: string) => {
    return new Date(dateTimeString).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      hour12: true
    });
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  const formatForInput = (iso) => {
    if (!iso) return '';
    const date = new Date(iso);
    const pad = n => n.toString().padStart(2, '0');
    return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`;
  };

  return (
    <div className="p-8 min-h-screen space-y-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl lg:text-3xl font-bold text-black flex items-center">
              {/* <CalendarIcon className="w-8 h-8 mr-3" /> */}
              Calendar Module
            </h1>
            <p className="text-gray-600 mt-1">Manage events, meetings, and availability</p>
          </div>
          <div className="flex flex-col sm:flex-row gap-2">
            <Dialog open={isCreateEventDialogOpen} onOpenChange={setIsCreateEventDialogOpen}>
              <DialogTrigger asChild>
                <Button>
                  <Plus className="w-4 h-4 mr-2" />
                  Create Event
                </Button>
              </DialogTrigger>
              <DialogContent className="rounded-3xl">
                <DialogHeader>
                  <DialogTitle>Create Event</DialogTitle>
                  <DialogDescription>Schedule a new event or meeting</DialogDescription>
                </DialogHeader>
                <form onSubmit={handleCreateEventSubmit} className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="md:col-span-2">
                      <Label htmlFor="title" className="text-black">Title *</Label>
                      <Input
                        id="title"
                        value={createEventForm.title}
                        onChange={(e) => setCreateEventForm({...createEventForm, title: e.target.value})}
                        placeholder="Enter event title"
                        className=" focus:ring-black"
                        required
                      />
                    </div>
                    <div className="md:col-span-2">
                      <Label htmlFor="description" className="text-black">Description</Label>
                      <Textarea
                        id="description"
                        value={createEventForm.description}
                        onChange={(e) => setCreateEventForm({...createEventForm, description: e.target.value})}
                        placeholder="Enter event description"
                        className=" focus:ring-black"
                        rows={3}
                      />
                    </div>

                    {/* Lead Selection */}
                    <div className="md:col-span-2 relative">
                      <Label className="text-black">Lead</Label>
                      <div className="relative">
                        <Input
                          type="text"
                          value={searchTerm}
                          onChange={(e) => setSearchTerm(e.target.value)}
                          placeholder="Search leads by name, email, company..."
                          className=" focus:ring-black pr-10"
                        />
                        {searchTerm && (
                          <button
                            type="button"
                            onClick={() => {
                              setSearchTerm('');
                              setCreateEventForm({
                                ...createEventForm,
                                lead_id: '',
                                lead_name: '',
                                lead_email: '',
                                lead_phone: '',
                                lead_company: ''
                              });
                            }}
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
                                onClick={() => {
                                  setCreateEventForm({
                                    ...createEventForm,
                                    lead_id: lead.id.toString(),
                                    lead_name: lead.full_name,
                                    lead_email: lead.email,
                                    lead_phone: lead.phone,
                                    lead_company: lead.company
                                  });
                                  setSearchTerm(lead.full_name);
                                  setShowLeadResults(false);
                                }}
                                className="w-full text-left px-3 py-2 hover:bg-gray-100 rounded-md transition-colors flex flex-col"
                              >
                                <span className="font-medium">{lead.full_name}</span>
                                <span className="text-sm text-gray-500">
                                  {lead.company} • {lead.email}
                                </span>
                              </button>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>

                    <div>
                      <Label htmlFor="start_datetime" className="text-black">Start Date & Time *</Label>
                      <Input
                        id="start_datetime"
                        type="datetime-local"
                        value={createEventForm.start_datetime}
                        onChange={(e) => setCreateEventForm({...createEventForm, start_datetime: e.target.value})}
                        className=" focus:ring-black"
                        required
                      />
                    </div>
                    <div>
                      <Label htmlFor="end_datetime" className="text-black">End Date & Time *</Label>
                      <Input
                        id="end_datetime"
                        type="datetime-local"
                        value={createEventForm.end_datetime}
                        onChange={(e) => setCreateEventForm({...createEventForm, end_datetime: e.target.value})}
                        className=" focus:ring-black"
                        required
                      />
                    </div>
                    <div>
                      <Label htmlFor="event_type" className="text-black">Event Type *</Label>
                      <Select value={createEventForm.event_type} onValueChange={(value) => setCreateEventForm({...createEventForm, event_type: value})}>
                        <SelectTrigger className="">
                          <SelectValue placeholder="Select event type" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="meeting">Meeting</SelectItem>
                          <SelectItem value="call">Call</SelectItem>
                          <SelectItem value="demo">Demo</SelectItem>
                          <SelectItem value="follow_up">Follow-up</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label htmlFor="priority" className="text-black">Priority *</Label>
                      <Select value={createEventForm.priority} onValueChange={(value) => setCreateEventForm({...createEventForm, priority: value})}>
                        <SelectTrigger className="">
                          <SelectValue placeholder="Select priority" />
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
                      <Label htmlFor="location" className="text-black">Location</Label>
                      <Input
                        id="location"
                        value={createEventForm.location}
                        onChange={(e) => setCreateEventForm({...createEventForm, location: e.target.value})}
                        placeholder="Enter location"
                        className=" focus:ring-black"
                      />
                    </div>
                    <div>
                      <Label htmlFor="meeting_url" className="text-black">Meeting URL</Label>
                      <Input
                        id="meeting_url"
                        value={createEventForm.meeting_url}
                        onChange={(e) => setCreateEventForm({...createEventForm, meeting_url: e.target.value})}
                        placeholder="https://..."
                        className=" focus:ring-black"
                      />
                    </div>
                  </div>
                  <div className="flex justify-end gap-3">
                    <Button
                      type="button"
                      variant="outline"
                      onClick={() => setIsCreateEventDialogOpen(false)}
                      className=" text-black"
                    >
                      Cancel
                    </Button>
                    <Button
                      type="submit"
                      className="bg-black text-white hover:bg-gray-800"
                      disabled={isLoading}
                    >
                      {isLoading ? (
                        <>
                          <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                          Creating...
                        </>
                      ) : (
                        'Create Event'
                      )}
                    </Button>
                  </div>
                </form>
              </DialogContent>
            </Dialog>
            <Button 
              variant="outline" 
              className=" text-black hover:bg-gray-50"
              onClick={() => setIsAvailabilityDialogOpen(true)}
            >
              <Clock className="w-4 h-4 mr-2" />
              Check Availability
            </Button>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {isLoading ? (
            [...Array(4)].map((_, i) => (
              <Card key={i} className=" ">
                <CardContent className="p-6">
                  <Skeleton className="h-6 w-32 mb-2" />
                  <Skeleton className="h-8 w-20 mb-2" />
                </CardContent>
              </Card>
            ))
          ) : (
            <>
              <Card className=" ">
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-600">Today's Events</p>
                      <p className="text-2xl font-bold text-black">{calendarSummary?.events_by_day[getLocalDateString(new Date())]?.length || 0}</p>
                    </div>
                    <CalendarIcon className="w-8 h-8 text-black" />
                  </div>
                </CardContent>
              </Card>
              <Card className=" ">
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-600">This Week</p>
                      <p className="text-2xl font-bold text-black">{calendarSummary?.total_events || 0}</p>
                    </div>
                    <Clock className="w-8 h-8 text-black" />
                  </div>
                </CardContent>
              </Card>
              <Card className=" ">
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-600">Busiest Day</p>
                      <p className="text-sm font-bold text-black">{calendarSummary?.busiest_day || "None"}</p>
                    </div>
                    <User className="w-8 h-8 text-black" />
                  </div>
                </CardContent>
              </Card>
              <Card className=" ">
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-600">Total Duration</p>
                      <p className="text-sm font-bold text-black">{calendarSummary?.total_duration_minutes || 0} minutes</p>
                    </div>
                    <MapPin className="w-8 h-8 text-black" />
                  </div>
                </CardContent>
              </Card>
            </>
          )}
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Calendar Widget */}
          <Card className="  lg:col-span-1 h-fit">
            <CardHeader>
              <CardTitle className="text-black">Calendar View</CardTitle>
              <CardDescription>Select a date to view events</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="w-full flex flex-col items-center">
                <div className="w-full max-w-xs md:max-w-sm lg:max-w-full">
                  <Calendar
                    mode="single"
                    selected={selectedDate}
                    onSelect={handleDateSelect}
                    className="rounded-md border  w-full"
                    modifiers={{
                      hasEvents: calendarSummary?.events_by_day
                        ? Object.keys(calendarSummary.events_by_day).map(date => new Date(date))
                        : []
                    }}
                    modifiersClassNames={{
                      hasEvents: "bg-blue-100 text-blue-900 font-bold"
                    }}
                  />
                </div>
                {/* Event indicators */}
                <div className="mt-4 space-y-2 w-full">
                  <h4 className="font-semibold text-black">Event Types</h4>
                  <div className="flex flex-wrap gap-2">
                    <div className="flex items-center gap-1">
                      <div className="w-3 h-3 bg-blue-500 rounded"></div>
                      <span className="text-xs">Meeting</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <div className="w-3 h-3 bg-green-500 rounded"></div>
                      <span className="text-xs">Call</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <div className="w-3 h-3 bg-purple-500 rounded"></div>
                      <span className="text-xs">Demo</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <div className="w-3 h-3 bg-orange-500 rounded"></div>
                      <span className="text-xs">Follow-up</span>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Events List and Filters */}
          <div className="lg:col-span-2 flex flex-col gap-6">
            {/* Selected Date Events */}
            {selectedDate && (
              <Card className=" ">
                <CardHeader>
                  <CardTitle className="text-black">
                    Events on {selectedDate.toLocaleDateString()}
                  </CardTitle>
                  <CardDescription>
                    {getEventsForDate(selectedDate).length} event(s) scheduled
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {isLoading ? (
                    <div className="space-y-3">
                      {[...Array(3)].map((_, i) => (
                        <Skeleton key={i} className="h-16 w-full mb-2" />
                      ))}
                    </div>
                  ) : error ? (
                    <p className="text-red-500 text-center py-8">{error}</p>
                  ) : getEventsForDate(selectedDate).length > 0 ? (
                    <div className="space-y-3">
                      {getEventsForDate(selectedDate).map((event) => (
                        <div key={event.id} className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition-colors cursor-pointer" onClick={() => navigate(`/calendar/events/${event.id}`)}>
                          <div className="flex items-center justify-between">
                            <div className="flex-1">
                              <div className="flex items-center gap-2 mb-2">
                                <div className={`w-3 h-3 rounded ${getCalendarEventColor(event.type)}`}></div>
                                <h3 className="font-semibold text-black">{event.title}</h3>
                                <Badge className={getEventTypeColor(event.type)}>
                                  {event.type}
                                </Badge>
                                <Badge className={getPriorityColor(event.priority)}>
                                  {event.priority}
                                </Badge>
                              </div>
                              <div className="text-sm text-gray-600 space-y-1">
                                <div className="flex items-center gap-2">
                                  <Clock className="w-4 h-4" />
                                  {event.start_time} ({event.duration} minutes)
                                </div>
                                <div className="flex items-center gap-2">
                                  <User className="w-4 h-4" />
                                  {event.lead_name || "N/A"}
                                </div>
                                <div className="flex items-center gap-2">
                                  <MapPin className="w-4 h-4" />
                                  {event.location || "N/A"}
                                </div>
                              </div>
                            </div>
                            <div className="flex gap-2">
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={(e) => { e.stopPropagation(); handleDeleteEvent(event); }}
                                className="border-red-300 text-red-700 hover:bg-red-50"
                              >
                                <Trash2 className="w-4 h-4" />
                              </Button>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-gray-500 text-center py-8">No events scheduled for this date</p>
                  )}
                </CardContent>
              </Card>
            )}

            {/* Upcoming Events */}
            <Card className=" ">
              <CardHeader className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                  <CardTitle className="text-black">All Upcoming Events</CardTitle>
                  <CardDescription>
                    Showing {filteredUpcomingEventsBySearch.length} of {allEvents.length} events
                  </CardDescription>
                </div>
                <div className="relative w-full sm:w-[300px] mt-2 sm:mt-0">
                  <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                  <Input
                    placeholder="Search events..."
                    value={searchUpcoming}
                    onChange={e => setSearchUpcoming(e.target.value)}
                    className="pl-10 rounded-2xl border-0 bg-muted/50"
                  />
                </div>
              </CardHeader>
              <CardContent>
                {isLoading ? (
                  <div className="space-y-3">
                    {[...Array(5)].map((_, i) => (
                      <Skeleton key={i} className="h-16 w-full mb-2" />
                    ))}
                  </div>
                ) : error ? (
                  <p className="text-red-500 text-center py-8">{error}</p>
                ) : filteredUpcomingEventsBySearch.length > 0 ? (
                  <div className="space-y-4">
                    {filteredUpcomingEventsBySearch.map((event) => (
                      <div 
                        key={event.id} 
                        className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition-colors cursor-pointer"
                        onClick={() => navigate(`/calendar/events/${event.id}`)}
                      >
                        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-2">
                              <div className={`w-3 h-3 rounded ${getCalendarEventColor(event.type)}`}></div>
                              <h3 className="font-semibold text-black">{event.title}</h3>
                              <Badge className={getEventTypeColor(event.type)}>
                                {event.type}
                              </Badge>
                              <Badge className={getPriorityColor(event.priority)}>
                                {event.priority}
                              </Badge>
                            </div>
                            <div className="text-sm text-gray-600 space-y-1">
                              <div className="flex items-center gap-2">
                                <Clock className="w-4 h-4" />
                                {event.start_time} - {event.date} ({event.duration} minutes)
                              </div>
                              <div className="flex items-center gap-2">
                                <User className="w-4 h-4" />
                                {event.lead_name || "N/A"}
                              </div>
                              <div className="flex items-center gap-2">
                                <MapPin className="w-4 h-4" />
                                {event.location || "N/A"}
                              </div>
                            </div>
                          </div>
                          <div className="flex flex-col sm:flex-row gap-2">
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={(e) => { e.stopPropagation(); handleDeleteEvent(event); }}
                              className="border-red-300 text-red-700 hover:bg-red-50"
                            >
                              <Trash2 className="w-4 h-4 mr-1" />
                              Delete
                            </Button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-gray-500 text-center py-8">No events found</p>
                )}
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Availability Check Dialog */}
        <Dialog open={isAvailabilityDialogOpen} onOpenChange={setIsAvailabilityDialogOpen}>
          <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>Check Availability</DialogTitle>
              <DialogDescription>Find available time slots for scheduling</DialogDescription>
            </DialogHeader>
            <div className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="start_date" className="text-black">Start Date *</Label>
                  <Input
                    id="start_date"
                    type="date"
                    value={availabilityForm.start_date}
                    onChange={(e) => setAvailabilityForm({...availabilityForm, start_date: e.target.value})}
                    className=" focus:ring-black"
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="end_date" className="text-black">End Date *</Label>
                  <Input
                    id="end_date"
                    type="date"
                    value={availabilityForm.end_date}
                    onChange={(e) => setAvailabilityForm({...availabilityForm, end_date: e.target.value})}
                    className=" focus:ring-black"
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="duration_minutes" className="text-black">Duration (minutes) *</Label>
                  <Select value={availabilityForm.duration_minutes.toString()} onValueChange={(value) => setAvailabilityForm({...availabilityForm, duration_minutes: parseInt(value)})}>
                    <SelectTrigger className="">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="15">15 minutes</SelectItem>
                      <SelectItem value="30">30 minutes</SelectItem>
                      <SelectItem value="45">45 minutes</SelectItem>
                      <SelectItem value="60">1 hour</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label htmlFor="buffer_minutes" className="text-black">Buffer Minutes</Label>
                  <Input
                    id="buffer_minutes"
                    type="number"
                    value={availabilityForm.buffer_minutes}
                    onChange={(e) => setAvailabilityForm({...availabilityForm, buffer_minutes: parseInt(e.target.value) || 0})}
                    placeholder="15"
                    className=" focus:ring-black"
                  />
                </div>
              </div>

              <Button
                onClick={handleCheckAvailability}
                className="w-full bg-black text-white hover:bg-gray-800"
                disabled={isLoading}
              >
                {isLoading ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Checking Availability...
                  </>
                ) : (
                  <>
                    <Search className="w-4 h-4 mr-2" />
                    Check Availability
                  </>
                )}
              </Button>

              {/* Availability Results */}
              {showAvailabilityResults && availabilityData && (
                <div className="space-y-4">
                  <div className="grid grid-cols-3 gap-4">
                    <div className="text-center">
                      <div className="text-2xl font-bold text-green-600">{availabilityData.available_count}</div>
                      <div className="text-sm text-gray-600">Available Slots</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-red-600">{availabilityData.busy_count}</div>
                      <div className="text-sm text-gray-600">Busy Slots</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-blue-600">{availabilityData.total_slots}</div>
                      <div className="text-sm text-gray-600">Total Slots</div>
                    </div>
                  </div>

                  {Object.entries(availabilityData.slots_by_day).map(([date, slots]: [string, any[]]) => (
                    <div key={date} className="border rounded-lg p-4">
                      <h3 className="font-semibold mb-2">{formatDate(date)}</h3>
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
                        {slots.map((slot, index) => (
                          <div
                            key={index}
                            className={`border rounded-lg p-3 ${
                              slot.is_available 
                                ? 'border-green-200 bg-green-50' 
                                : 'border-red-200 bg-red-50'
                            }`}
                          >
                            <div className="flex items-center justify-between mb-2">
                              <div className="font-medium text-black">
                                {formatTime(slot.start_datetime)} - {formatTime(slot.end_datetime)}
                              </div>
                              <Badge className={
                                slot.is_available 
                                  ? 'bg-green-100 text-green-700 border-green-200' 
                                  : 'bg-red-100 text-red-700 border-red-200'
                              }>
                                {slot.is_available ? 'Available' : 'Busy'}
                              </Badge>
                            </div>
                            {slot.is_available && (
                              <Button
                                size="sm"
                                className="w-full mt-2 bg-green-600 text-white hover:bg-green-700"
                                onClick={() => {
                                  const formatForInput = (iso) => {
                                    if (!iso) return '';
                                    const date = new Date(iso);
                                    const pad = n => n.toString().padStart(2, '0');
                                    return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`;
                                  };
                                  setCreateEventForm(prev => ({
                                    ...prev,
                                    start_datetime: formatForInput(slot.start_datetime),
                                    end_datetime: formatForInput(slot.end_datetime)
                                  }));
                                  setIsAvailabilityDialogOpen(false);
                                  setIsCreateEventDialogOpen(true);
                                }}
                              >
                                <Plus className="w-3 h-3 mr-1" />
                                Schedule
                              </Button>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </DialogContent>
        </Dialog>

        {/* Delete Confirmation Modal */}
        <Dialog open={isDeleteModalOpen} onOpenChange={setIsDeleteModalOpen}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Delete Event</DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <p className="text-gray-600">
                Are you sure you want to delete "{selectedEvent?.title}"? This action cannot be undone.
              </p>
              <div className="flex justify-end gap-3">
                <Button variant="outline" onClick={() => setIsDeleteModalOpen(false)} className=" text-black">
                  Cancel
                </Button>
                <Button onClick={confirmDeleteEvent} className="bg-red-600 text-white hover:bg-red-700">
                  Delete Event
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
};

export default CalendarModule;