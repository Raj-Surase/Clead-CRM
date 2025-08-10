import { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from '@/components/ui/form';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { authApi, Profile as ProfileType, Company } from '@/lib/authApi';
import { useAuth } from '@/contexts/AuthContext';
import { toast } from 'sonner';
import { User, Settings } from 'lucide-react';

interface PersonalForm {
  first_name: string;
  last_name: string;
  phone: string;
  timezone: string;
}

interface CompanyForm {
  company_name: string;
  company_size: string;
  industry: string;
  website: string;
  description: string;
  address: string;
  city: string;
  state: string;
  country: string;
  postal_code: string;
}

const companySizes = [
  { value: '1-10', label: '1-10 employees' },
  { value: '11-50', label: '11-50 employees' },
  { value: '51-200', label: '51-200 employees' },
  { value: '201-500', label: '201-500 employees' },
  { value: '501-1000', label: '501-1000 employees' },
  { value: '1001-5000', label: '1001-5000 employees' },
  { value: '5000+', label: '5000+ employees' },
];

const industries = [
  'Technology',
  'Healthcare',
  'Finance',
  'Education',
  'Retail',
  'Manufacturing',
  'Real Estate',
  'Marketing',
  'Other',
];

const timezones = [
  'UTC', 'America/New_York', 'America/Los_Angeles', 'America/Chicago',
  'Europe/London', 'Europe/Paris', 'Europe/Berlin', 'Asia/Tokyo',
  'Asia/Shanghai', 'Asia/Kolkata', 'Australia/Sydney'
];

export default function Profile() {
  const [isPersonalLoading, setIsPersonalLoading] = useState(false);
  const [isCompanyLoading, setIsCompanyLoading] = useState(false);
  const { user, refreshUser, logout } = useAuth();

  const personalForm = useForm<PersonalForm>({
    defaultValues: {
      first_name: '',
      last_name: '',
      phone: '',
      timezone: 'UTC',
    },
  });

  const companyForm = useForm<CompanyForm>({
    defaultValues: {
      company_name: '',
      company_size: '',
      industry: '',
      website: '',
      description: '',
      address: '',
      city: '',
      state: '',
      country: '',
      postal_code: '',
    },
  });

  useEffect(() => {
    const loadData = async () => {
      try {
        const [profile, company] = await Promise.all([
          authApi.getProfile(),
          authApi.getCompany().catch(() => ({}))
        ]);

        personalForm.reset({
          first_name: (profile as ProfileType).first_name || '',
          last_name: (profile as ProfileType).last_name || '',
          phone: (profile as ProfileType).phone || '',
          timezone: (profile as ProfileType).timezone || 'UTC',
        });

        companyForm.reset({
          company_name: (company as Company).company_name || '',
          company_size: (company as Company).company_size || '',
          industry: (company as Company).industry || '',
          website: (company as Company).website || '',
          description: (company as any).description || '',
          address: (company as any).address || '',
          city: (company as any).city || '',
          state: (company as any).state || '',
          country: (company as any).country || '',
          postal_code: (company as any).postal_code || '',
        });
      } catch (error) {
        toast.error('Failed to load profile data');
      }
    };

    loadData();
  }, [personalForm, companyForm]);

  const onPersonalSubmit = async (data: PersonalForm) => {
    setIsPersonalLoading(true);
    try {
      await authApi.updateProfile(data);
      await refreshUser();
      toast.success('Personal information updated successfully');
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Failed to update personal information');
    } finally {
      setIsPersonalLoading(false);
    }
  };

  const onCompanySubmit = async (data: CompanyForm) => {
    setIsCompanyLoading(true);
    try {
      await authApi.updateCompany(data);
      toast.success('Company information updated successfully');
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Failed to update company information');
    } finally {
      setIsCompanyLoading(false);
    }
  };

  const handleLogout = async () => {
    try {
      await logout();
      toast.success('Logged out successfully');
    } catch (error) {
      toast.error('Failed to logout');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-muted/20 p-4 md:p-8">
      <div className="max-w-4xl mx-auto space-y-8">
        <div>
          <h1 className="text-3xl font-bold">Profile Settings</h1>
          <p className="text-muted-foreground mt-2">Manage your account and company information</p>
          </div>
        <Tabs defaultValue="personal" className="w-full">
          <TabsList className="grid w-full grid-cols-2 h-14 rounded-md">
          <TabsTrigger
            value="personal"
            className="flex items-center justify-center gap-2 h-full px-4 text-sm font-medium hover:bg-gray-200 data-[state=active]:bg-white rounded-md transition"
          >
            <User className="h-4 w-4" />
            Personal
          </TabsTrigger>
          <TabsTrigger
            value="company"
            className="flex items-center justify-center gap-2 h-full px-4 text-sm font-medium hover:bg-gray-200 data-[state=active]:bg-white rounded-md transition"
          >
            <Settings className="h-4 w-4" />
            Company
          </TabsTrigger>
        </TabsList>


          <TabsContent value="personal">
            <Card>
              <CardHeader>
                <CardTitle>Personal Information</CardTitle>
                <CardDescription>Update your personal details</CardDescription>
              </CardHeader>
              <CardContent>
                <Form {...personalForm}>
                  <form onSubmit={personalForm.handleSubmit(onPersonalSubmit)} className="space-y-6">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <FormField
                        control={personalForm.control}
                        name="first_name"
                        rules={{ required: 'First name is required' }}
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel>First Name</FormLabel>
                            <FormControl>
                              <Input {...field} />
                            </FormControl>
                            <FormMessage />
                          </FormItem>
                        )}
                      />

                      <FormField
                        control={personalForm.control}
                        name="last_name"
                        rules={{ required: 'Last name is required' }}
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel>Last Name</FormLabel>
                            <FormControl>
                              <Input {...field} />
                            </FormControl>
                            <FormMessage />
                          </FormItem>
                        )}
                      />
                    </div>

                    <FormField
                      control={personalForm.control}
                      name="phone"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Phone Number</FormLabel>
                          <FormControl>
                            <Input {...field} />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    <FormField
                      control={personalForm.control}
                      name="timezone"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Timezone</FormLabel>
                          <Select onValueChange={field.onChange} value={field.value} defaultValue={field.value}>
                            <FormControl>
                              <SelectTrigger>
                                <SelectValue placeholder="Select timezone" />
                              </SelectTrigger>
                            </FormControl>
                            <SelectContent>
                              {timezones.map((tz) => (
                                <SelectItem key={tz} value={tz}>
                                  {tz}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    <div className="flex justify-between">
                      <Button type="button" variant="destructive" onClick={handleLogout}>
                        Logout
                      </Button>
                      <Button type="submit" disabled={isPersonalLoading}>
                        {isPersonalLoading ? 'Saving...' : 'Save Changes'}
                      </Button>
                    </div>
                  </form>
                </Form>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="company">
            <Card>
              <CardHeader>
                <CardTitle>Company Information</CardTitle>
                <CardDescription>Update your company details</CardDescription>
              </CardHeader>
              <CardContent>
                <Form {...companyForm}>
                  <form onSubmit={companyForm.handleSubmit(onCompanySubmit)} className="space-y-6">
                    <FormField
                      control={companyForm.control}
                      name="company_name"
                      rules={{ required: 'Company name is required' }}
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Company Name</FormLabel>
                          <FormControl>
                            <Input {...field} />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <FormField
                        control={companyForm.control}
                        name="company_size"
                        rules={{ required: 'Company size is required' }}
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel>Company Size</FormLabel>
                            <Select onValueChange={field.onChange} value={field.value} defaultValue={field.value}>
                              <FormControl>
                                <SelectTrigger>
                                  <SelectValue placeholder="Select size" />
                                </SelectTrigger>
                              </FormControl>
                              <SelectContent>
                                {companySizes.map((size) => (
                                  <SelectItem key={size.value} value={size.value}>
                                    {size.label}
                                  </SelectItem>
                                ))}
                              </SelectContent>
                            </Select>
                            <FormLabel/>
                          </FormItem>
                        )}
                      />

                      <FormField
                        control={companyForm.control}
                        name="industry"
                        rules={{ required: 'Industry is required' }}
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel>Industry</FormLabel>
                            <Select onValueChange={field.onChange} value={field.value} defaultValue={field.value}>
                              <FormControl>
                                <SelectTrigger>
                                  <SelectValue placeholder="Select industry" />
                                </SelectTrigger>
                              </FormControl>
                              <SelectContent>
                                {industries.map((industry) => (
                                  <SelectItem key={industry} value={industry}>
                                    {industry}
                                  </SelectItem>
                                ))}
                              </SelectContent>
                            </Select>
                            <FormMessage />
                          </FormItem>
                        )}
                      />
                    </div>

                    <FormField
                      control={companyForm.control}
                      name="website"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Website</FormLabel>
                          <FormControl>
                            <Input {...field} placeholder="https://your-company.com" />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    <FormField
                      control={companyForm.control}
                      name="description"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Description</FormLabel>
                          <FormControl>
                            <Input {...field} />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    <FormField
                      control={companyForm.control}
                      name="address"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Address</FormLabel>
                          <FormControl>
                            <Input {...field} />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <FormField
                        control={companyForm.control}
                        name="city"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel>City</FormLabel>
                            <FormControl>
                              <Input {...field} />
                            </FormControl>
                            <FormMessage />
                          </FormItem>
                        )}
                      />

                      <FormField
                        control={companyForm.control}
                        name="state"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel>State</FormLabel>
                            <FormControl>
                              <Input {...field} />
                            </FormControl>
                            <FormMessage />
                          </FormItem>
                        )}
                      />
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <FormField
                        control={companyForm.control}
                        name="country"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel>Country</FormLabel>
                            <FormControl>
                              <Input {...field} />
                            </FormControl>
                            <FormMessage />
                          </FormItem>
                        )}
                      />

                      <FormField
                        control={companyForm.control}
                        name="postal_code"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel>Postal Code</FormLabel>
                            <FormControl>
                              <Input {...field} />
                            </FormControl>
                            <FormMessage />
                          </FormItem>
                        )}
                      />
                    </div>

                    <Button type="submit" disabled={isCompanyLoading}>
                      {isCompanyLoading ? 'Saving...' : 'Save Changes'}
                    </Button>
                  </form>
                </Form>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}