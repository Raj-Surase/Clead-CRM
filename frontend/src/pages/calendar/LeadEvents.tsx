import { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { ArrowLeft, User, Calendar, Clock, MapPin, Plus, Search, Mail, Phone, Building } from "lucide-react";
import { calendarApi, leadApi, Event, Lead } from "@/lib/api";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import LeadEventCreateDialog from "./LeadEventCreateDialog";
import { Skeleton } from "@/components/ui/skeleton";

const LeadEvents = () => {
  const { leadId } = useParams<{ leadId: string }>();
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [eventTypeFilter, setEventTypeFilter] = useState("all");
  const [events, setEvents] = useState<Event[]>([]);
  const [lead, setLead] = useState<Lead | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);

  useEffect(() => {
    const fetchLeadData = async () => {
      if (!leadId) return;
      setLoading(true);
      try {
        // Fetch lead information
        const fetchedLead = await leadApi.getLead(Number(leadId));
        setLead(fetchedLead as Lead);

        // Fetch lead events
        const fetchedEvents = await calendarApi().getLeadEvents(Number(leadId));
        setEvents(fetchedEvents);
      } catch (err) {
        setError("Failed to fetch lead data or events");
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchLeadData();
  }, [leadId]);

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

  const getStatusColor = (status: string) => {
    switch (status) {
      case "completed": return "bg-green-50 text-green-700 border-green-200";
      case "scheduled": return "bg-blue-50 text-blue-700 border-blue-200";
      case "tentative": return "bg-yellow-50 text-yellow-700 border-yellow-200";
      case "cancelled": return "bg-red-50 text-red-700 border-red-200";
      default: return "bg-gray-50 text-gray-700 border-gray-200";
    }
  };

  const filteredEvents = events.filter(event => {
    const matchesSearch = event.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         (event.notes && event.notes.toLowerCase().includes(searchQuery.toLowerCase()));
    const matchesStatus = statusFilter === "all" || event.status === statusFilter;
    const matchesType = eventTypeFilter === "all" || event.event_type === eventTypeFilter;
    return matchesSearch && matchesStatus && matchesType;
  });

  const upcomingEvents = filteredEvents.filter(event => event.is_upcoming);
  const completedEvents = filteredEvents.filter(event => event.status === "completed");

  if (loading) {
    return (
      <div className="min-h-screen p-4 lg:p-8">
        <div className="max-w-7xl mx-auto space-y-6">
          <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4">
            <Skeleton className="h-10 w-32 mb-4" />
            <div className="flex-1">
              <Skeleton className="h-8 w-48 mb-2" />
              <Skeleton className="h-4 w-64" />
            </div>
            <Skeleton className="h-10 w-40" />
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <Skeleton className="h-64 w-full" />
            <div className="lg:col-span-2 space-y-6">
              <Skeleton className="h-20 w-full mb-4" />
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Skeleton className="h-24 w-full" />
                <Skeleton className="h-24 w-full" />
                <Skeleton className="h-24 w-full" />
              </div>
              <Skeleton className="h-96 w-full" />
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return <div className="min-h-screen  p-4 lg:p-8">{error}</div>;
  }

  return (
    <div className="min-h-screen  p-4 lg:p-8">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4">
          <Link to="/calendar">
            <Button variant="outline" size="sm" className=" text-black hover:bg-gray-50">
              <ArrowLeft className="w-4 h-4 mr-2" />
            </Button>
          </Link>
          <div className="flex-1">
            <h1 className="text-2xl lg:text-3xl font-bold text-black flex items-center">
              <User className="w-8 h-8 mr-3" />
              Lead Events
            </h1>
            <p className="text-gray-600 mt-1">Events and meetings for {lead?.full_name || "Lead"}</p>
          </div>
          <Link to="#" onClick={() => setIsCreateDialogOpen(true)}>
            <Button className="bg-black text-white hover:bg-gray-800">
              <Plus className="w-4 h-4 mr-2" />
              Create Event for Lead
            </Button>
          </Link>
        </div>

        {/* Lead Profile */}
        <Card className=" ">
          <CardHeader>
            <CardTitle className="text-black flex items-center">
              <User className="w-5 h-5 mr-2" />
              Lead Information
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <h3 className="font-semibold text-black text-lg">{lead?.full_name || "N/A"}</h3>
              <p className="text-gray-600">{lead?.job_title || "N/A"}</p>
            </div>
            <div className="space-y-3">
              <div className="flex items-center gap-3">
                <Building className="w-4 h-4 text-gray-600" />
                <div>
                  <div className="font-medium text-black">{lead?.company || "N/A"}</div>
                  <div className="text-sm text-gray-600">{lead?.industry || "N/A"}</div>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <Mail className="w-4 h-4 text-gray-600" />
                <div>
                  <div className="text-black">{lead?.email || "N/A"}</div>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <Phone className="w-4 h-4 text-gray-600" />
                <div>
                  <div className="text-black">{lead?.phone || "N/A"}</div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Events Statistics */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card className=" ">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Total Events</p>
                  <p className="text-2xl font-bold text-black">{events.length}</p>
                </div>
                <Calendar className="w-8 h-8 text-black" />
              </div>
            </CardContent>
          </Card>
          <Card className=" ">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Upcoming</p>
                  <p className="text-2xl font-bold text-blue-600">{upcomingEvents.length}</p>
                </div>
                <Clock className="w-8 h-8 text-blue-600" />
              </div>
            </CardContent>
          </Card>
          <Card className=" ">
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Completed</p>
                  <p className="text-2xl font-bold text-green-600">{completedEvents.length}</p>
                </div>
                <MapPin className="w-8 h-8 text-green-600" />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Events Timeline - full width */}
        <Card className="w-full">
          <CardHeader>
            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
              <CardTitle className="text-black">Events Timeline</CardTitle>
              <Input
                placeholder="Search events..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full md:w-64 focus:ring-black"
              />
            </div>
            <CardDescription>
              Showing {filteredEvents.length} of {events.length} events
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {filteredEvents.map((event) => (
                <Link key={event.id} to={`/calendar/events/${event.id}`} className="block">
                  <div className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition-colors cursor-pointer">
                    <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <h3 className="font-semibold text-black">{event.title}</h3>
                          <Badge className={getEventTypeColor(event.event_type)}>
                            {event.event_type}
                          </Badge>
                          <Badge className={getPriorityColor(event.priority)}>
                            {event.priority}
                          </Badge>
                          <Badge className={getStatusColor(event.status)}>
                            {event.status}
                          </Badge>
                        </div>
                        <div className="text-sm text-gray-600 space-y-1">
                          <div className="flex items-center gap-2">
                            <Clock className="w-4 h-4" />
                            {event.start_datetime} - {event.end_datetime.split(' ')[1]}
                          </div>
                          <div className="flex items-center gap-2">
                            <MapPin className="w-4 h-4" />
                            {event.location || "N/A"}
                          </div>
                          {event.notes && (
                            <div className="mt-2">
                              <span className="font-medium">Notes: </span>
                              {event.notes}
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
      <LeadEventCreateDialog
        open={isCreateDialogOpen}
        onOpenChange={setIsCreateDialogOpen}
        lead={lead}
        onEventCreated={() => {
          setIsCreateDialogOpen(false);
          // Refresh events after creation
          if (leadId) {
            calendarApi().getLeadEvents(Number(leadId)).then(setEvents);
          }
        }}
      />
    </div>
  );
};

export default LeadEvents;