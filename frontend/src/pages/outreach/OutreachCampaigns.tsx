import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Plus, Search, Eye, Trash2, Loader2 } from "lucide-react";
import { Link, useSearchParams, useNavigate } from "react-router-dom";
import { toast } from "@/hooks/use-toast";
import { crmApi } from "@/lib/crmAPI";
import { Dialog as ConfirmDialog, DialogContent as ConfirmDialogContent, DialogHeader as ConfirmDialogHeader, DialogTitle as ConfirmDialogTitle } from "@/components/ui/dialog";
import { authApi } from "@/lib/authApi";
import { Skeleton } from "@/components/ui/skeleton";

interface Campaign {
  id: number;
  name: string;
  description: string;
  status: string;
  start_date: string;
  end_date: string;
  created_at: string;
  updated_at: string;
  total_leads: number;
}

export default function OutreachCampaigns() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [filteredCampaigns, setFilteredCampaigns] = useState<Campaign[]>([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(searchParams.get('create') === 'true');
  const [newCampaign, setNewCampaign] = useState({
    name: "",
    description: "",
    start_date: "",
    end_date: "",
    status: "active",
  });
  const [deleteCampaignId, setDeleteCampaignId] = useState<number | null>(null);
  const [deleteLoading, setDeleteLoading] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  // Fetch campaigns from API
  useEffect(() => {
    const fetchCampaigns = async () => {
      try {
        setIsLoading(true);
        setError(null);
        const userId = await authApi.getUserId();
        const response = await crmApi.getCampaigns(userId);
        setCampaigns(response as Campaign[]);
        setFilteredCampaigns(response as Campaign[]);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch campaigns');
        toast({
          variant: "destructive",
          title: "Error",
          description: "Failed to fetch campaigns. Please try again.",
        });
      } finally {
        setIsLoading(false);
      }
    };

    fetchCampaigns();
  }, []);

  // Filter campaigns by search term
  useEffect(() => {
    let filtered = campaigns;
    
    if (searchTerm) {
      filtered = filtered.filter((campaign) =>
        campaign.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        campaign.description?.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }
    
    setFilteredCampaigns(filtered);
  }, [campaigns, searchTerm]);

  const handleCreateCampaign = async () => {
    try {
      const userId = await authApi.getUserId();
      const response = await crmApi.createCampaign(userId,  {
        name: newCampaign.name,
        description: newCampaign.description,
        start_date: `${newCampaign.start_date}T00:00:00Z`,
        end_date: newCampaign.end_date ? `${newCampaign.end_date}T00:00:00Z` : undefined,
        status: newCampaign.status,
        user_id: userId,
      });
      setCampaigns(prev => [response as Campaign, ...prev]);
      setNewCampaign({
        name: "",
        description: "",
        start_date: "",
        end_date: "",
        status: "active",
      });
      setIsCreateModalOpen(false);
      
      toast({
        title: "Campaign Created",
        description: "Your campaign has been created successfully.",
      });
    } catch (err) {
      toast({
        variant: "destructive",
        title: "Error",
        description: "Failed to create campaign. Please try again.",
      });
    }
  };

  const handleDeleteCampaign = async () => {
    if (deleteCampaignId == null) return;
    setDeleteLoading(true);
    setDeleteError(null);
    try {
      const userId = await authApi.getUserId();
      await crmApi.deleteCampaign(userId, deleteCampaignId);
      setCampaigns(prev => prev.filter(campaign => campaign.id !== deleteCampaignId));
      setDeleteCampaignId(null);
      toast({
        title: "Campaign Deleted",
        description: "The campaign has been deleted successfully.",
      });
    } catch (err) {
      setDeleteError(err instanceof Error ? err.message : "Failed to delete campaign. Please try again.");
    } finally {
      setDeleteLoading(false);
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

  return (
    <div className="p-8 min-h-screen space-y-6">
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div>
            <h1 className="text-3xl font-bold">Outreach Campaigns</h1>
            <p className="text-muted-foreground">Create and manage your outreach campaigns</p>
          </div>
          
          <Dialog open={isCreateModalOpen} onOpenChange={setIsCreateModalOpen}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="w-4 h-4 mr-2" />
                Create Campaign
              </Button>
            </DialogTrigger>
            <DialogContent className="rounded-3xl">
              <DialogHeader>
                <DialogTitle>Create New Campaign</DialogTitle>
              </DialogHeader>
              <div className="space-y-4">
                <div>
                  <Label>Name *</Label>
                  <Input
                    value={newCampaign.name}
                    onChange={(e) => setNewCampaign(prev => ({ ...prev, name: e.target.value }))}
                    className="rounded-2xl border-0 bg-muted/50"
                    placeholder="Campaign name"
                  />
                </div>
                <div>
                  <Label>Description</Label>
                  <Textarea
                    value={newCampaign.description}
                    onChange={(e) => setNewCampaign(prev => ({ ...prev, description: e.target.value }))}
                    className="rounded-2xl border-0 bg-muted/50"
                    placeholder="Campaign description"
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Start Date *</Label>
                    <Input
                      type="date"
                      value={newCampaign.start_date}
                      onChange={(e) => setNewCampaign(prev => ({ ...prev, start_date: e.target.value }))}
                      className="rounded-2xl border-0 bg-muted/50"
                    />
                  </div>
                  <div>
                    <Label>End Date</Label>
                    <Input
                      type="date"
                      value={newCampaign.end_date}
                      onChange={(e) => setNewCampaign(prev => ({ ...prev, end_date: e.target.value }))}
                      className="rounded-2xl border-0 bg-muted/50"
                    />
                  </div>
                </div>
                <div>
                  <Label>Status *</Label>
                  <Select value={newCampaign.status} onValueChange={(value) => setNewCampaign(prev => ({ ...prev, status: value }))}>
                    <SelectTrigger className="rounded-2xl border-0 bg-muted/50">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="rounded-2xl">
                      <SelectItem value="active">Active</SelectItem>
                      <SelectItem value="inactive">Inactive</SelectItem>
                      <SelectItem value="paused">Paused</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="flex gap-2">
                  <Button 
                    onClick={handleCreateCampaign}
                    disabled={!newCampaign.name || !newCampaign.start_date}
                  >
                    Create Campaign
                  </Button>
                  <Button 
                    variant="outline" 
                    onClick={() => setIsCreateModalOpen(false)}
                    className="rounded-2xl border-0 bg-muted/50"
                  >
                    Cancel
                  </Button>
                </div>
              </div>
            </DialogContent>
          </Dialog>
        </div>

        {/* Campaigns Table */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>
                Campaigns ({filteredCampaigns.length})
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
                  <TableHead>Name</TableHead>
                  <TableHead>Description</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Start Date</TableHead>
                  <TableHead>Total Leads</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead>Actions</TableHead>
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
                ) : filteredCampaigns.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={7} className="text-center py-8 text-muted-foreground">
                      No campaigns found
                    </TableCell>
                  </TableRow>
                ) : (
                  filteredCampaigns.map((campaign) => (
                    <TableRow 
                      key={campaign.id}
                      className="cursor-pointer hover:bg-accent/50"
                      onClick={() => navigate(`/outreach/campaigns/${campaign.id}`)}
                    >
                      <TableCell className="font-medium">{campaign.name}</TableCell>
                      <TableCell>{campaign.description}</TableCell>
                      <TableCell>
                        <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                          campaign.status === 'active' 
                            ? 'bg-green-100 text-green-800' 
                            : campaign.status === 'paused'
                            ? 'bg-yellow-100 text-yellow-800'
                            : 'bg-gray-100 text-gray-800'
                        }`}>
                          {campaign.status}
                        </span>
                      </TableCell>
                      <TableCell>{new Date(campaign.start_date).toLocaleDateString()}</TableCell>
                      <TableCell>{campaign.total_leads}</TableCell>
                      <TableCell>{new Date(campaign.created_at).toLocaleDateString()}</TableCell>
                      <TableCell>
                        <Button 
                          size="sm" 
                          variant="outline" 
                          className="text-destructive hover:bg-destructive/10"
                          onClick={(e) => {
                            e.stopPropagation();
                            setDeleteCampaignId(campaign.id);
                          }}
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </CardContent>
        </Card>

        {/* Confirm Delete Dialog */}
        <ConfirmDialog open={deleteCampaignId !== null} onOpenChange={open => { if (!open) setDeleteCampaignId(null); }}>
          <ConfirmDialogContent className="rounded-3xl" aria-describedby={undefined}>
            <ConfirmDialogHeader>
              <ConfirmDialogTitle>Confirm Campaign Deletion</ConfirmDialogTitle>
            </ConfirmDialogHeader>
            <div className="py-4">Are you sure you want to delete this campaign? This action cannot be undone.</div>
            {deleteError && <div className="text-destructive text-sm mb-2">{deleteError}</div>}
            <div className="flex gap-2 justify-end">
              <Button variant="outline" onClick={() => setDeleteCampaignId(null)} disabled={deleteLoading}>
                Cancel
              </Button>
              <Button variant="destructive" onClick={handleDeleteCampaign} disabled={deleteLoading}>
                {deleteLoading ? 'Deleting...' : 'Delete'}
              </Button>
            </div>
          </ConfirmDialogContent>
        </ConfirmDialog>
      </div>
    </div>
  );
}