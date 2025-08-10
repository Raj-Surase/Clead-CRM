import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Input } from "@/components/ui/input";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Plus, Search, Edit, Trash2 } from "lucide-react";
import { toast } from "@/hooks/use-toast";
import { crmApi, Template } from "@/lib/api";
import { Dialog as ConfirmDialog, DialogContent as ConfirmDialogContent, DialogHeader as ConfirmDialogHeader, DialogTitle as ConfirmDialogTitle } from "@/components/ui/dialog";
import { Dialog as ViewDialog, DialogContent as ViewDialogContent, DialogHeader as ViewDialogHeader, DialogTitle as ViewDialogTitle } from "@/components/ui/dialog";
import { useAuth } from "@/contexts/AuthContext";
import { authApi } from "@/lib/authApi";
import { Skeleton } from "@/components/ui/skeleton";

export default function OutreachTemplates() {
  const { user } = useAuth();
  const [templates, setTemplates] = useState<Template[]>([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [editingTemplate, setEditingTemplate] = useState<Template | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [templateForm, setTemplateForm] = useState({
    name: "",
    subject: "",
    content: "",
  });
  const [deleteTemplateId, setDeleteTemplateId] = useState<number | null>(null);
  const [deleteLoading, setDeleteLoading] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);
  const [viewTemplate, setViewTemplate] = useState<Template | null>(null);
  const [isViewModalOpen, setIsViewModalOpen] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setIsLoading(true);
        setError(null);
        const userId = await authApi.getUserId();
        const templatesResponse = await crmApi.getOutreachTemplates(userId);
        setTemplates(templatesResponse);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'An error occurred while fetching data');
        toast({
          title: "Error",
          description: "Failed to load data. Please try again.",
          variant: "destructive"
        });
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, []);

  const handleSaveTemplate = async () => {
    try {
      const templateData = {
        ...templateForm,
        user_id: user?.id
      };
      const userId = await authApi.getUserId();
      if (editingTemplate) {
        const updatedTemplate = await crmApi.updateOutreachTemplate(userId, editingTemplate.id, templateData);
        setTemplates(prev => prev.map((t) => 
          t.id === editingTemplate.id ? updatedTemplate : t
        ));
        toast({
          title: "Template Updated",
          description: "Template has been updated successfully.",
        });
      } else {
        const newTemplate = await crmApi.createOutreachTemplate(userId, templateData);
        setTemplates(prev => [newTemplate, ...prev]);
        toast({
          title: "Template Created",
          description: "Template has been created successfully.",
        });
      }
      
      setTemplateForm({ name: "", subject: "", content: "" });
      setEditingTemplate(null);
      setIsCreateModalOpen(false);
    } catch (err) {
      toast({
        title: "Error",
        description: editingTemplate 
          ? "Failed to update template. Please try again." 
          : "Failed to create template. Please try again.",
        variant: "destructive"
      });
    }
  };

  const handleEditTemplate = (template: Template) => {
    setTemplateForm({
      name: template.name,
      subject: template.subject || "",
      content: template.content
    });
    setEditingTemplate(template);
    setIsCreateModalOpen(true);
  };

  const handleDeleteTemplate = async () => {
    if (deleteTemplateId == null) return;
    setDeleteLoading(true);
    setDeleteError(null);
    try {
      const userId = await authApi.getUserId();
      await crmApi.deleteOutreachTemplate(userId, deleteTemplateId);
      setTemplates(prev => prev.filter((template) => template.id !== deleteTemplateId));
      setDeleteTemplateId(null);
      toast({
        title: "Template Deleted",
        description: "Template has been deleted successfully.",
      });
    } catch (err) {
      setDeleteError(err instanceof Error ? err.message : "Failed to delete template. Please try again.");
    } finally {
      setDeleteLoading(false);
    }
  };

  // Compute filtered templates directly in render
  const filteredTemplates = templates.filter((template) => {
    const matchesSearch =
      template.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      template.subject?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      template.content?.toLowerCase().includes(searchTerm.toLowerCase());

    return matchesSearch;
  });

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
  //       <p>Loading...</p>
  //     </div>
  //   );
  // }

  return (
    <div className="p-8 min-h-screen space-y-6">
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div>
            <h1 className="text-2xl md:text-3xl font-bold">Templates</h1>
            <p className="text-muted-foreground text-sm md:text-base">Manage outreach templates</p>
          </div>
          
          <Dialog open={isCreateModalOpen} onOpenChange={(open) => {
            setIsCreateModalOpen(open);
            if (!open) {
              setEditingTemplate(null);
              setTemplateForm({ name: "", subject: "", content: "" });
            }
          }}>
            <DialogTrigger asChild>
              <Button className="w-full sm:w-auto">
                <Plus className="w-4 h-4 mr-2" />
                Create Template
              </Button>
            </DialogTrigger>
            <DialogContent className="rounded-3xl mx-4 max-w-lg">
              <DialogHeader>
                <DialogTitle>
                  {editingTemplate ? "Edit Template" : "Create New Template"}
                </DialogTitle>
              </DialogHeader>
              <div className="space-y-4">
                <div>
                  <Label>Name *</Label>
                  <Input
                    value={templateForm.name}
                    onChange={(e) => setTemplateForm(prev => ({ ...prev, name: e.target.value }))}
                    className="rounded-2xl border-0 bg-muted/50"
                    placeholder="Template name"
                  />
                </div>
                {/* <div>
                  <Label>Platform *</Label>
                  <Select 
                    value={templateForm.platform_id} 
                    onValueChange={(value) => setTemplateForm(prev => ({ ...prev, platform_id: value }))}
                  >
                    <SelectTrigger className="rounded-2xl border-0 bg-muted/50">
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
                </div> */}
                <div>
                  <Label>Subject *</Label>
                  <Input
                    value={templateForm.subject}
                    onChange={(e) => setTemplateForm(prev => ({ ...prev, subject: e.target.value }))}
                    className="rounded-2xl border-0 bg-muted/50"
                    placeholder="Message subject"
                  />
                </div>
                <div>
                  <Label>Content *</Label>
                  <Textarea
                    value={templateForm.content}
                    onChange={(e) => setTemplateForm(prev => ({ ...prev, content: e.target.value }))}
                    className="rounded-2xl border-0 bg-muted/50 min-h-32"
                    placeholder="Message content (use {{name}} for personalization)"
                  />
                </div>
                
                <div className="flex flex-col sm:flex-row gap-2">
                  <Button 
                    onClick={handleSaveTemplate}
                    disabled={!templateForm.name || !templateForm.subject || !templateForm.content }
                    className="flex-1"
                  >
                    {editingTemplate ? "Update Template" : "Create Template"}
                  </Button>
                  <Button 
                    variant="outline" 
                    onClick={() => setIsCreateModalOpen(false)}
                    className="rounded-2xl border-0 bg-muted/50 flex-1 sm:flex-none"
                  >
                    Cancel
                  </Button>
                </div>
              </div>
            </DialogContent>
          </Dialog>
        </div>

        {/* Templates Table */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg md:text-xl">
                Templates ({filteredTemplates.length})
              </CardTitle>
              <div className="relative w-[300px]">
                <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search templates..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10 rounded-2xl border-0 bg-muted/50"
                />
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="min-w-32">Name</TableHead>
                    <TableHead className="min-w-32 hidden sm:table-cell">Subject</TableHead>
                    {/* <TableHead className="min-w-24 hidden md:table-cell">Platform</TableHead> */}
                    {/* <TableHead className="min-w-20 hidden lg:table-cell">Created By</TableHead> */}
                    {/* <TableHead className="min-w-32 hidden xl:table-cell">Created</TableHead> */}
                    <TableHead className="min-w-24">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {isLoading ? (
                    [...Array(5)].map((_, i) => (
                      <TableRow key={i}>
                        <TableCell><Skeleton className="h-4 w-32" /></TableCell>
                        <TableCell className="hidden sm:table-cell"><Skeleton className="h-4 w-32" /></TableCell>
                        <TableCell><Skeleton className="h-4 w-24" /></TableCell>
                      </TableRow>
                    ))
                  ) : filteredTemplates.length > 0 ? (
                    filteredTemplates.map((template) => (
                      <TableRow key={template.id} className="cursor-pointer hover:bg-accent/50" onClick={() => {
                        setViewTemplate(template);
                        setIsViewModalOpen(true);
                      }}>
                        <TableCell className="font-medium">
                          <div>
                            <div className="font-medium">{template.name}</div>
                            <div className="text-sm text-muted-foreground sm:hidden">
                              {template.subject}
                            </div>
                          </div>
                        </TableCell>
                        <TableCell className="hidden sm:table-cell">{template.subject}</TableCell>
                        <TableCell className="hidden xl:table-cell">{new Date(template.created_at).toLocaleString()}</TableCell>
                        <TableCell>
                          <div className="flex flex-col sm:flex-row gap-1">
                            <Button size="sm" variant="outline" className="rounded-2xl border-0 bg-muted/50 text-xs px-2"
                              onClick={(e) => {
                                e.stopPropagation();
                                handleEditTemplate(template);
                              }}>
                              <Edit className="w-3 h-3 sm:mr-1" />
                              <span className="hidden sm:inline">Edit</span>
                            </Button>
                            <Button size="sm" variant="outline" className="text-destructive hover:bg-destructive/10 text-xs px-2 rounded-2xl border-0 bg-muted/50"
                              onClick={(e) => {
                                e.stopPropagation();
                                setDeleteTemplateId(template.id);
                              }}>
                              <Trash2 className="w-3 h-3 sm:mr-1" />
                              <span className="hidden sm:inline">Delete</span>
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))
                  ) : (
                    <TableRow>
                      <TableCell colSpan={4} className="text-center py-8 text-muted-foreground">
                        No templates found.
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>

              </Table>
            </div>
          </CardContent>
        </Card>

        {/* View Template Dialog */}
        <ViewDialog open={isViewModalOpen} onOpenChange={setIsViewModalOpen}>
          <ViewDialogContent className="rounded-3xl">
            <ViewDialogHeader>
              <ViewDialogTitle>{viewTemplate?.name || 'Template Details'}</ViewDialogTitle>
            </ViewDialogHeader>
            {viewTemplate && (
              <div className="space-y-4">
                <div>
                  <Label className="text-sm text-muted-foreground">Platform</Label>
                  {/* <p>{viewTemplate.platform?.name || 'Unknown'}</p> */}
                </div>
                <div>
                  <Label className="text-sm text-muted-foreground">Subject</Label>
                  <p>{viewTemplate.subject}</p>
                </div>
                <div>
                  <Label className="text-sm text-muted-foreground">Content</Label>
                  <div className="bg-muted/50 p-4 rounded-2xl mt-1">
                    <p className="whitespace-pre-wrap">{viewTemplate.content}</p>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  {/* <div>
                    <Label className="text-sm text-muted-foreground">Created By</Label>
                    <p>{viewTemplate.created_by}</p>
                  </div> */}
                  <div>
                    <Label className="text-sm text-muted-foreground">Created At</Label>
                    <p>{new Date(viewTemplate.created_at).toLocaleString()}</p>
                  </div>
                </div>
                <div className="flex justify-end gap-2 pt-4">
                  <Button 
                    variant="outline" 
                    className="rounded-2xl border-0 bg-muted/50"
                    onClick={() => setIsViewModalOpen(false)}
                  >
                    Close
                  </Button>
                  <Button 
                    onClick={() => {
                      setIsViewModalOpen(false);
                      handleEditTemplate(viewTemplate);
                    }}
                  >
                    Edit Template
                  </Button>
                </div>
              </div>
            )}
          </ViewDialogContent>
        </ViewDialog>

        {/* Confirm Delete Dialog */}
        <ConfirmDialog open={deleteTemplateId !== null} onOpenChange={open => { if (!open) setDeleteTemplateId(null); }}>
          <ConfirmDialogContent className="rounded-3xl">
            <ConfirmDialogHeader>
              <ConfirmDialogTitle>Confirm Template Deletion</ConfirmDialogTitle>
            </ConfirmDialogHeader>
            <div className="py-4">Are you sure you want to delete this template? This action cannot be undone.</div>
            {deleteError && <div className="text-destructive text-sm mb-2">{deleteError}</div>}
            <div className="flex gap-2 justify-end">
              <Button 
                variant="outline" 
                onClick={() => setDeleteTemplateId(null)} 
                className="rounded-2xl border-0 bg-muted/50" 
                disabled={deleteLoading}
              >
                Cancel
              </Button>
              <Button 
                variant="destructive" 
                onClick={handleDeleteTemplate} 
                disabled={deleteLoading}
              >
                {deleteLoading ? 'Deleting...' : 'Delete'}
              </Button>
            </div>
          </ConfirmDialogContent>
        </ConfirmDialog>
      </div>
    </div>
  );
}