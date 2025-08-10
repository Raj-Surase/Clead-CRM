import { useState, useEffect, useImperativeHandle, forwardRef } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Search, ChevronLeft, ChevronRight, Edit, Trash2, User, Mail, Phone, Building, MapPin, Globe, ExternalLink } from "lucide-react";
import { leadApi } from "@/lib/api";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { useToast } from "@/hooks/use-toast";
import { Separator } from "@/components/ui/separator";
import { useDebounce } from "@/hooks/use-debounce";

interface LeadParserProps {
  onEditLead: (lead: any) => void;
}

const LeadParser = forwardRef<{ refresh: () => void }, LeadParserProps>(({ onEditLead }, ref) => {
  const [searchQuery, setSearchQuery] = useState("");
  const [leads, setLeads] = useState<any[]>([]);
  const [pagination, setPagination] = useState({
    page: 1,
    per_page: 10,
    total_pages: 1,
    total: 0
  });
  const [isTableLoading, setIsTableLoading] = useState(false);
  const { toast } = useToast();
  const [deleteLoading, setDeleteLoading] = useState(false);
  const [viewDialogOpen, setViewDialogOpen] = useState(false);
  const [viewLead, setViewLead] = useState<any>(null);

  // Add debounced values
  const debouncedSearch = useDebounce(searchQuery, 500);

  const fetchLeads = async () => {
    setIsTableLoading(true);
    try {
      const params: any = {
        page: pagination.page,
        per_page: pagination.per_page,
        search: debouncedSearch,
      };

      const leadsResponse = await leadApi.getLeads(params);
      setLeads(leadsResponse.leads || []);
      setPagination({
        page: leadsResponse.page,
        per_page: leadsResponse.per_page,
        total_pages: leadsResponse.total_pages,
        total: leadsResponse.total
      });
    } catch (e: any) {
      toast({ title: "Error", description: e.message, variant: "destructive" });
    }
    setIsTableLoading(false);
  };

  // Expose refresh function to parent
  useImperativeHandle(ref, () => ({
    refresh: fetchLeads
  }));

  // Initial data fetch
  useEffect(() => {
    fetchLeads();
  }, [debouncedSearch, pagination.page, pagination.per_page, toast]);

  const handlePageChange = (newPage: number) => {
    if (newPage >= 1 && newPage <= pagination.total_pages) {
      setPagination(prev => ({ ...prev, page: newPage }));
    }
  };

  const handleDelete = async (lead: any) => {
    if (!window.confirm(`Delete lead ${lead.full_name || lead.email}?`)) return;
    setDeleteLoading(true);
    try {
      await leadApi.deleteLead(lead.id);
      toast({ title: "Lead deleted", description: `${lead.full_name || lead.email} was deleted.` });
      setLeads((prev: any[]) => prev.filter(l => l.id !== lead.id));
    } catch (e: any) {
      toast({ title: "Delete failed", description: e.message, variant: "destructive" });
    }
    setDeleteLoading(false);
  };

  if (isTableLoading) {
    return <div className="text-center">Loading...</div>;
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-lg md:text-xl">Leads</CardTitle>
              <CardDescription className="text-sm">
                Showing {leads.length} of {pagination.total} leads
              </CardDescription>
            </div>
            <div className="flex items-center gap-4">
              <div className="relative">
                <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search by name, email, or company..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10 rounded-2xl border-0 bg-muted/50 w-[300px]"
                />
              </div>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="overflow-x-auto relative">
              {isTableLoading && (
                <div className="absolute inset-0 bg-white/50 flex items-center justify-center z-10">
                  <div className="text-sm text-gray-600">Loading...</div>
                </div>
              )}
              <table className="w-full">
                <thead>
                  <tr className="border-b border-border">
                    <th className="text-left p-3 font-medium text-black">Name</th>
                    <th className="text-left p-3 font-medium text-black hidden sm:table-cell">Email</th>
                    <th className="text-left p-3 font-medium text-black hidden md:table-cell">Company</th>
                    <th className="text-left p-3 font-medium text-black">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {leads.map((lead) => (
                    <tr
                      key={lead.id}
                      className="border-b border-border hover:bg-accent/50 cursor-pointer"
                      onClick={() => { setViewLead(lead); setViewDialogOpen(true); }}
                    >
                      <td className="p-3">
                        <div className="font-medium text-black">{lead.full_name || (lead.first_name && lead.last_name ? `${lead.first_name} ${lead.last_name}` : '-')}</div>
                        <div className="text-sm text-muted-foreground sm:hidden">{lead.email || '-'}</div>
                      </td>
                      <td className="p-3 text-muted-foreground hidden sm:table-cell">{lead.email || '-'}</td>
                      <td className="p-3 text-muted-foreground hidden md:table-cell">{lead.company || '-'}</td>
                      <td className="p-3 flex gap-2">
                        <Button size="sm" variant="outline" className="rounded-2xl border-0 bg-muted/50" onClick={e => { e.stopPropagation(); onEditLead(lead); }}>
                          <Edit className="w-4 h-4" />
                        </Button>
                        <Button size="sm" variant="destructive" disabled={deleteLoading} onClick={e => { e.stopPropagation(); handleDelete(lead); }}>
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
              <div className="text-sm text-muted-foreground">
                Showing {((pagination.page - 1) * pagination.per_page) + 1} to {Math.min(pagination.page * pagination.per_page, pagination.total)} of {pagination.total} leads
              </div>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handlePageChange(pagination.page - 1)}
                  disabled={pagination.page === 1}
                  className="rounded-2xl border-0 bg-muted/50"
                >
                  <ChevronLeft className="w-4 h-4" />
                  <span className="hidden sm:inline ml-1">Previous</span>
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handlePageChange(pagination.page + 1)}
                  disabled={pagination.page === pagination.total_pages}
                  className="rounded-2xl border-0 bg-muted/50"
                >
                  <span className="hidden sm:inline mr-1">Next</span>
                  <ChevronRight className="w-4 h-4" />
                </Button>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      <Dialog open={viewDialogOpen} onOpenChange={setViewDialogOpen}>
        <DialogContent className="rounded-3xl max-w-4xl">
          {viewLead && (
            <div className="space-y-6">
              <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4">
                <div className="flex-1">
                  <h1 className="text-2xl lg:text-3xl font-bold text-black">{viewLead.full_name || (viewLead.first_name && viewLead.last_name ? `${viewLead.first_name} ${viewLead.last_name}` : '-')}</h1>
                  <p className="text-gray-600 mt-1">{viewLead.job_title || '-'} at {viewLead.company || '-'}</p>
                </div>
              </div>
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2">
                  <Card>
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
                              {viewLead.email ? (
                                <a href={`mailto:${viewLead.email}`} className="font-medium text-black hover:text-blue-600">{viewLead.email}</a>
                              ) : (
                                <p className="font-medium text-black">-</p>
                              )}
                            </div>
                          </div>
                          <div className="flex items-start gap-3">
                            <Phone className="w-5 h-5 text-gray-600 mt-0.5" />
                            <div>
                              <p className="text-sm text-gray-600">Phone</p>
                              {viewLead.phone ? (
                                <a href={`tel:${viewLead.phone}`} className="font-medium text-black hover:text-blue-600">{viewLead.phone}</a>
                              ) : (
                                <p className="font-medium text-black">-</p>
                              )}
                            </div>
                          </div>
                          <div className="flex items-start gap-3">
                            <Phone className="w-5 h-5 text-gray-600 mt-0.5" />
                            <div>
                              <p className="text-sm text-gray-600">Mobile</p>
                              {viewLead.mobile ? (
                                <a href={`tel:${viewLead.mobile}`} className="font-medium text-black hover:text-blue-600">{viewLead.mobile}</a>
                              ) : (
                                <p className="font-medium text-black">-</p>
                              )}
                            </div>
                          </div>
                          <div className="flex items-start gap-3">
                            <Building className="w-5 h-5 text-gray-600 mt-0.5" />
                            <div>
                              <p className="text-sm text-gray-600">Company & Role</p>
                              <p className="font-medium text-black">{viewLead.company || '-'}</p>
                              <p className="text-sm text-gray-600">{viewLead.job_title || '-'}</p>
                            </div>
                          </div>
                        </div>
                        <div className="space-y-4">
                          <div className="flex items-start gap-3">
                            <MapPin className="w-5 h-5 text-gray-600 mt-0.5" />
                            <div>
                              <p className="text-sm text-gray-600">Location</p>
                              <p className="font-medium text-black">{viewLead.city || '-'}, {viewLead.country || '-'}</p>
                              <p className="text-sm text-gray-600">{viewLead.industry || '-'}</p>
                            </div>
                          </div>
                          <div className="flex items-start gap-3">
                            <Globe className="w-5 h-5 text-gray-600 mt-0.5" />
                            <div>
                              <p className="text-sm text-gray-600">LinkedIn</p>
                              {viewLead.linkedin_url ? (
                                <a href={viewLead.linkedin_url} target="_blank" rel="noopener noreferrer" className="font-medium text-black hover:text-blue-600 flex items-center">
                                  View Profile
                                  <ExternalLink className="w-3 h-3 ml-1" />
                                </a>
                              ) : (
                                <p className="font-medium text-black">-</p>
                              )}
                            </div>
                          </div>
                          <div className="flex items-start gap-3">
                            <Globe className="w-5 h-5 text-gray-600 mt-0.5" />
                            <div>
                              <p className="text-sm text-gray-600">Website</p>
                              {viewLead.website ? (
                                <a href={viewLead.website} target="_blank" rel="noopener noreferrer" className="font-medium text-black hover:text-blue-600 flex items-center">
                                  Visit Site
                                  <ExternalLink className="w-3 h-3 ml-1" />
                                </a>
                              ) : (
                                <p className="font-medium text-black">-</p>
                              )}
                            </div>
                          </div>
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
                    </CardContent>
                  </Card>
                </div>
                <div className="space-y-6">
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-black text-lg">Source Information</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div>
                        <p className="text-sm text-gray-600 mb-1">Source File</p>
                        <p className="text-black font-medium">{viewLead.source_file_name || '-'}</p>
                        <p className="text-sm text-gray-600">Row {viewLead.source_file_row || '-'}</p>
                      </div>
                      <Separator className="bg-gray-200" />
                      <div>
                        <p className="text-sm text-gray-600 mb-1">Created</p>
                        <p className="text-black font-medium">{new Date(viewLead.created_at).toLocaleDateString()}</p>
                      </div>
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
    </div>
  );
});

LeadParser.displayName = "LeadParser";

export default LeadParser;