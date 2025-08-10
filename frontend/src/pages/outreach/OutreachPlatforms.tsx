import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Link, Settings, Mail, Plus, Loader2, Unlink, Trash } from "lucide-react";
import { Link as RouterLink } from "react-router-dom";
import { toast } from "@/hooks/use-toast";
import { crmApi, Platform, PlatformConnection } from "@/lib/api";
import { authApi } from "@/lib/authApi";
import { Skeleton } from "@/components/ui/skeleton";

interface HealthStatus {
  outreach_db: string;
  lead_parser_db: string;
  calendar_db: string;
  integration_status: string;
}

interface Stats {
  totalPlatforms: number;
  connectedPlatforms: number;
}

export default function OutreachPlatforms() {
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [platforms, setPlatforms] = useState<PlatformConnection[]>([]);
  const [healthStatus, setHealthStatus] = useState<HealthStatus>({ 
    outreach_db: "healthy", 
    lead_parser_db: "healthy", 
    calendar_db: "healthy", 
    integration_status: "healthy" 
  });
  const [stats, setStats] = useState<Stats>({
    totalPlatforms: 0,
    connectedPlatforms: 0,
  });
  const [isConnectModalOpen, setIsConnectModalOpen] = useState(false);
  const [isAddPlatformModalOpen, setIsAddPlatformModalOpen] = useState(false);
  const [newPlatform, setNewPlatform] = useState({ name: "", description: "", username: "", password: "" });
  const [connectCredentials, setConnectCredentials] = useState({ platformId: 0, username: "", password: "", platformName: "" });
  // const userId = await ;
  
  useEffect(() => {
    const fetchData = async () => {
      try {
        setIsLoading(true);
        setError(null);

        const userId = await authApi.getUserId();

        const [availablePlatforms, healthData] = await Promise.all([
          crmApi.getUserAvailablePlatforms(String(userId)),
          crmApi.getIntegrationHealth(String(userId))
        ]);

        setPlatforms(availablePlatforms);
        setHealthStatus(healthData);
        setStats({
          totalPlatforms: availablePlatforms.length,
          connectedPlatforms: availablePlatforms.filter(p => p.is_connected).length,
        });
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : "An error occurred while fetching platform data";
        setError(errorMessage);
        toast({
          variant: "destructive",
          title: "Error",
          description: errorMessage,
        });
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, []);

  const handleConnect = async () => {
    try {
      setIsLoading(true);
      const userId = await authApi.getUserId();
      const response = await crmApi.authenticatePlatform(
        String(userId),
        {
          platform_id: connectCredentials.platformId,
          username: connectCredentials.username,
          password: connectCredentials.password
        }
      );

      if (response.success) {
        const updatedPlatforms = await crmApi.getUserAvailablePlatforms(String(userId));
        setPlatforms(updatedPlatforms);
        setStats(prev => ({
          ...prev,
          connectedPlatforms: updatedPlatforms.filter(p => p.is_connected).length
        }));
        setIsConnectModalOpen(false);
        setConnectCredentials({ platformId: 0, username: "", password: "", platformName: "" });
        toast({
          title: "Platform Connected",
          description: `Successfully connected ${connectCredentials.username} to ${connectCredentials.platformName}.`,
        });
      }
    } catch (err) {
      toast({
        variant: "destructive",
        title: "Error",
        description: err instanceof Error ? err.message : "Failed to connect platform.",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleDelete = async (platformId: number) => {
    try {
      setIsLoading(true);
      const userId = await authApi.getUserId();
      const response = await crmApi.deletePlatform(
        String(userId),
        platformId
      );
      // The deletePlatform API does not return a response body (void), so we should not check for `if (response)`.
      // Instead, after successful deletion, proceed to update the platforms list and UI state.
      const updatedPlatforms = await crmApi.getUserAvailablePlatforms(String(userId));
      setPlatforms(updatedPlatforms);
      setStats(prev => ({
        ...prev,
        connectedPlatforms: updatedPlatforms.filter(p => p.is_connected).length
      }));
      setIsConnectModalOpen(false);
      setConnectCredentials({ platformId: 0, username: "", password: "", platformName: "" });
      toast({
        title: "Platform Deleted",
        description: `Successfully deleted ${connectCredentials.platformName}.`,
      });
    } catch (err) {
      toast({
        variant: "destructive",
        title: "Error",
        description: err instanceof Error ? err.message : "Failed to delete platform.",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleDisconnect = async (platformId: number) => {
    try {
      setIsLoading(true);
      const userId = await authApi.getUserId();
      await crmApi.disconnectPlatform(String(userId), platformId);
      const updatedPlatforms = await crmApi.getUserAvailablePlatforms(String(userId));
      setPlatforms(updatedPlatforms);
      setStats(prev => ({
        ...prev,
        connectedPlatforms: updatedPlatforms.filter(p => p.is_connected).length
      }));
      toast({
        title: "Platform Disconnected",
        description: "Platform has been disconnected successfully.",
      });
    } catch (err) {
      toast({
        variant: "destructive",
        title: "Error",
        description: err instanceof Error ? err.message : "Failed to disconnect platform.",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleAddPlatform = async () => {
    try {
      setIsLoading(true);
      const userId = await authApi.getUserId();
      const platformData = {
        name: newPlatform.name,
        description: newPlatform.description,
        user_id: String(userId),
        username: newPlatform.username || undefined,
        password: newPlatform.password || undefined
      };
      await crmApi.createPlatform(String(userId), platformData);

      const updatedPlatforms = await crmApi.getUserAvailablePlatforms(String(userId));
      setPlatforms(updatedPlatforms);
      setStats(prev => ({
        ...prev,
        totalPlatforms: updatedPlatforms.length,
        connectedPlatforms: updatedPlatforms.filter(p => p.is_connected).length
      }));
      setIsAddPlatformModalOpen(false);
      setNewPlatform({ name: "", description: "", username: "", password: "" });
      toast({
        title: "Platform Added",
        description: newPlatform.username ? 
          `New email platform "${newPlatform.name}" has been added and authenticated successfully.` :
          `New email platform "${newPlatform.name}" has been added successfully.`
      });
    } catch (err) {
      toast({
        variant: "destructive",
        title: "Error",
        description: err instanceof Error ? err.message : "Failed to add platform.",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const openConnectModal = (platform: PlatformConnection) => {
    setConnectCredentials({
      platformId: platform.platform.id,
      username: "",
      password: "",
      platformName: platform.platform.name
    });
    setIsConnectModalOpen(true);
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
    <div className="p-6 min-h-screen">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-black">Email Platform Management</h1>
            <p className="text-gray-600">Manage your email outreach accounts</p>
          </div>
          <div className="flex gap-3">
            <Button
              className="bg-black text-white hover:bg-gray-800"
              onClick={() => setIsAddPlatformModalOpen(true)}
              disabled={isLoading}
            >
              <Plus className="w-4 h-4 mr-2" />
              Add Email Account
            </Button>
            {/* <Button
              asChild
              variant="outline"
              className=" text-black hover:bg-gray-100"
              disabled={isLoading}
            >
              <RouterLink to="/outreach/settings">
                <Settings className="w-4 h-4 mr-2" />
                Settings
              </RouterLink>
            </Button> */}
          </div>
        </div>

        {/* Email Setup Guide */}
        {/* <Card className="border-2 border-yellow-200 bg-yellow-50">
          <CardHeader>
            <CardTitle className="text-black flex items-center gap-2">
              <Mail className="w-5 h-5" />
              Email Account Setup Guide
            </CardTitle>
            <CardDescription>
              Connect your email accounts using app-specific passwords
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <p className="text-sm text-gray-700">
                To connect your email account, enable 2-factor authentication and generate an app-specific password:
              </p>
              <ul className="list-disc list-inside text-sm text-gray-700 space-y-1">
                <li><a href="https://support.google.com/accounts/answer/185833" className="text-blue-600 hover:underline">Gmail: Generate an app password</a></li>
                <li><a href="https://support.microsoft.com/en-us/account-billing/manage-app-passwords-for-two-step-verification-d6dc8c6d-6a7e-4b8a-9b3a-2d4b7a8b9c2e" className="text-blue-600 hover:underline">Outlook: Create an app password</a></li>
              </ul>
            </div>
          </CardContent>
        </Card> */}

        {/* Statistics Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Card className="">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-black">Total Email Accounts</CardTitle>
              <Settings className="h-4 w-4 text-black" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-black">
                {isLoading ? (
                  <Skeleton className="h-8 w-16" />
                ) : (
                  stats.totalPlatforms
                )}
              </div>
            </CardContent>
          </Card>
          <Card className="">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-black">Connected Accounts</CardTitle>
              <Link className="h-4 w-4 text-black" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-black">
                {isLoading ? (
                  <Skeleton className="h-8 w-16" />
                ) : (
                  stats.connectedPlatforms
                )}
              </div>
            </CardContent>
          </Card>
          {/* <Card className="">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-black">System Status</CardTitle>
              <Settings className="h-4 w-4 text-black" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-black">
                {isLoading ? (
                  <Loader2 className="h-6 w-6 animate-spin" />
                ) : (
                  healthStatus.integration_status
                )}
              </div>
            </CardContent>
          </Card> */}
        </div>

        {/* Platforms Table */}
        <Card className="">
          <CardHeader>
            <CardTitle className="text-black">Email Accounts</CardTitle>
            <CardDescription>Manage your connected email accounts</CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="text-black">Account Name</TableHead>
                  <TableHead className="text-black">Email Address</TableHead>
                  <TableHead className="text-black">Status</TableHead>
                  <TableHead className="text-black">Connected At</TableHead>
                  <TableHead className="text-black">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {isLoading ? (
                  [...Array(5)].map((_, i) => (
                    <TableRow key={i}>
                      {[...Array(5)].map((_, j) => (
                        <TableCell key={j}><Skeleton className="h-4 w-24" /></TableCell>
                      ))}
                    </TableRow>
                  ))
                ) : platforms.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={5} className="text-gray-500 text-center">
                      No email accounts configured
                    </TableCell>
                  </TableRow>
                ) : (
                  platforms.map((platform) => (
                    <TableRow key={platform.platform.id}>
                      <TableCell className="text-black">
                          {platform.platform.name}
                      </TableCell>
                      <TableCell className="text-black">{platform.username || 'N/A'}</TableCell>
                      <TableCell className="text-black">
                        {platform.is_connected ? (
                          <span className="text-green-600">Connected</span>
                        ) : (
                          <span className="text-red-600">Not Connected</span>
                        )}
                      </TableCell>
                      <TableCell className="text-black">
                        {platform.connected_at ? new Date(platform.connected_at).toLocaleDateString() : 'N/A'}
                      </TableCell>
                      <TableCell>
                        <div className="flex gap-2">
                          {!platform.is_connected ? (
                            <Button
                              size="sm"
                              className="bg-black text-white hover:bg-gray-800"
                              onClick={() => openConnectModal(platform)}
                              disabled={isLoading}
                            >
                              <Link className="w-4 h-4 mr-1" />
                              Connect
                            </Button>
                          ) : (
                            <Button
                              variant="outline"
                              size="sm"
                              className="-red-300 text-red-600 hover:bg-red-50"
                              onClick={() => handleDisconnect(platform.platform.id)}
                              disabled={isLoading}
                            >
                              <Unlink className="w-4 h-4 mr-1" />
                              Disconnect
                            </Button>
                          )}
                          <Button
                            variant="outline"
                            size="sm"
                            className="-red-300 text-red-600 hover:bg-red-50"
                            onClick={() => handleDelete(platform.platform.id)}
                            disabled={isLoading}
                          >
                            <Trash className="w-4 h-4 mr-1" />
                            Delete
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </CardContent>
        </Card>

        {/* Connect Platform Modal */}
        <Dialog open={isConnectModalOpen} onOpenChange={setIsConnectModalOpen}>
          <DialogContent className="sm:max-w-[425px]">
            <DialogHeader>
              <DialogTitle>Connect Email Account: {connectCredentials.platformName}</DialogTitle>
            </DialogHeader>
            <div className="grid gap-4 py-4">
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="username" className="text-right">Email Address</Label>
                <Input
                  id="username"
                  type="email"
                  value={connectCredentials.username}
                  onChange={(e) => setConnectCredentials({ ...connectCredentials, username: e.target.value })}
                  className="col-span-3"
                  placeholder="your.email@example.com"
                />
              </div>
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="password" className="text-right">App Password</Label>
                <Input
                  id="password"
                  type="password"
                  value={connectCredentials.password}
                  onChange={(e) => setConnectCredentials({ ...connectCredentials, password: e.target.value })}
                  className="col-span-3"
                  placeholder="Enter app-specific password"
                />
              </div>
            </div>
            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => setIsConnectModalOpen(false)}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                className="bg-black text-white hover:bg-gray-800"
                onClick={handleConnect}
                disabled={isLoading || !connectCredentials.username || !connectCredentials.password || !connectCredentials.platformId}
              >
                {isLoading ? <Loader2 className="h-4 w-4 animate-spin mr-1" /> : null}
                Connect
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Add Platform Modal */}
        <Dialog open={isAddPlatformModalOpen} onOpenChange={setIsAddPlatformModalOpen}>
          <DialogContent className="sm:max-w-[425px]">
            <DialogHeader>
              <DialogTitle>Add New Email Account</DialogTitle>
            </DialogHeader>
            <div className="grid gap-4 py-4">
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="name" className="text-right">Account Name</Label>
                <Input
                  id="name"
                  value={newPlatform.name}
                  onChange={(e) => setNewPlatform({ ...newPlatform, name: e.target.value })}
                  className="col-span-3"
                  placeholder="e.g., Work Gmail"
                />
              </div>
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="description" className="text-right">Description</Label>
                <Input
                  id="description"
                  value={newPlatform.description}
                  onChange={(e) => setNewPlatform({ ...newPlatform, description: e.target.value })}
                  className="col-span-3"
                  placeholder="e.g., Primary work email"
                />
              </div>
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="username" className="text-right">Email Address</Label>
                <Input
                  id="username"
                  type="email"
                  value={newPlatform.username}
                  onChange={(e) => setNewPlatform({ ...newPlatform, username: e.target.value })}
                  className="col-span-3"
                  placeholder="your.email@example.com"
                />
              </div>
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="password" className="text-right">App Password</Label>
                <Input
                  id="password"
                  type="password"
                  value={newPlatform.password}
                  onChange={(e) => setNewPlatform({ ...newPlatform, password: e.target.value })}
                  className="col-span-3"
                  placeholder="Enter app-specific password"
                />
              </div>
            </div>
            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => setIsAddPlatformModalOpen(false)}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                className="bg-black text-white hover:bg-gray-800"
                onClick={handleAddPlatform}
                disabled={isLoading || !newPlatform.name}
              >
                {isLoading ? <Loader2 className="h-4 w-4 animate-spin mr-1" /> : null}
                Add Account
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
}