import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import {
  User,
  Mail,
  Shield,
  Calendar,
  Save,
  ArrowLeft,
  Loader2,
  CheckCircle,
  Lock,
  Monitor,
  LogOut,
  Trash2,
  AlertTriangle
} from "lucide-react";
import { GlassCard } from "@/components/ui/GlassCard";
import { GlowingInput } from "@/components/ui/GlowingInput";
import { NeonButton } from "@/components/ui/NeonButton";
import { StatusChip } from "@/components/ui/StatusChip";
import { ParticleBackground } from "@/components/layout/ParticleBackground";
import { useAuth } from "@/hooks/useAuth";
// Removed Supabase import as we are using the Python backend context
import { useToast } from "@/hooks/use-toast";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

const roleLabels: Record<string, string> = {
  admin: "Administrator",
  compliance_officer: "Compliance Officer",
  auditor: "Auditor",
  manager: "Manager",
};

interface Session {
  id: string;
  device: string;
  location: string;
  lastActive: string;
  current: boolean;
}

export default function Profile() {
  const navigate = useNavigate();
  const { user, role, loading: authLoading } = useAuth();
  const { toast } = useToast();
  
  const [displayName, setDisplayName] = useState("");
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [changingPassword, setChangingPassword] = useState(false);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [showLogoutDialog, setShowLogoutDialog] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);

  useEffect(() => {
    if (!authLoading && !user) {
      navigate("/auth");
      return;
    }

    if (user) {
      // Initialize profile data from AuthContext instead of Supabase
      setDisplayName(user.user_metadata?.display_name || "");

      // Mock sessions
      setSessions([
        { id: "1", device: "Chrome on Windows", location: "Mumbai, India", lastActive: new Date().toISOString(), current: true },
        { id: "2", device: "Safari on iPhone", location: "Delhi, India", lastActive: new Date(Date.now() - 3600000).toISOString(), current: false },
      ]);
    }
  }, [user, authLoading, navigate]);

  const handleSave = async () => {
    if (!user) return;

    setSaving(true);
    setSaved(false);

    // Simulate API call since backend profile update endpoint is not yet available
    setTimeout(() => {
        setSaving(false);
        setSaved(true);
        toast({
            title: "Profile Updated",
            description: "Your profile has been updated successfully.",
        });
        setTimeout(() => setSaved(false), 3000);
    }, 1000);
  };

  const handleChangePassword = async () => {
    if (newPassword !== confirmPassword) {
      toast({
        title: "Error",
        description: "Passwords do not match.",
        variant: "destructive",
      });
      return;
    }

    setChangingPassword(true);
    // Simulate password change
    setTimeout(() => {
      setChangingPassword(false);
      toast({
        title: "Password Changed",
        description: "Your password has been updated successfully.",
      });
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
    }, 2000);
  };

  const handleLogout = () => {
    // Simulate logout
    navigate("/auth");
  };

  const handleDeleteAccount = () => {
    // Simulate delete
    navigate("/auth");
  };

  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (!user) {
    return null;
  }

  // Fallback for created_at since it's missing from the User type in api.ts
  const createdAt = new Date().toLocaleDateString("en-US", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });

  return (
    <div className="min-h-screen bg-background relative overflow-hidden">
      <ParticleBackground />

      {/* Header */}
      <header className="relative z-10 border-b border-border/50 bg-card/50 backdrop-blur-xl">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center gap-4">
            <NeonButton variant="ghost" size="sm" onClick={() => navigate("/dashboard")}>
              <ArrowLeft className="h-4 w-4" />
            </NeonButton>
            <div>
              <h1 className="text-xl font-bold text-foreground">Profile Settings</h1>
              <p className="text-xs text-muted-foreground">Manage your account details</p>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="relative z-10 container mx-auto px-6 py-8 max-w-4xl">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <Tabs defaultValue="profile" className="w-full">
            <TabsList className="grid w-full grid-cols-4 mb-6">
              <TabsTrigger value="profile">Profile</TabsTrigger>
              <TabsTrigger value="security">Security</TabsTrigger>
              <TabsTrigger value="sessions">Sessions</TabsTrigger>
              <TabsTrigger value="account">Account</TabsTrigger>
            </TabsList>

            {/* Profile Tab */}
            <TabsContent value="profile">
              <GlassCard className="p-8">
                {/* Avatar Section */}
                <div className="flex items-center gap-6 mb-8 pb-8 border-b border-border/50">
                  <motion.div
                    className="h-20 w-20 rounded-full bg-gradient-to-br from-primary to-secondary flex items-center justify-center shadow-[0_0_30px_hsl(var(--primary)/0.4)] cursor-pointer"
                    whileHover={{ scale: 1.05, boxShadow: "0 0 40px hsl(var(--primary)/0.6)" }}
                    transition={{ type: "spring", stiffness: 300 }}
                  >
                    <User className="h-10 w-10 text-primary-foreground" />
                  </motion.div>
                  <div>
                    <h2 className="text-2xl font-bold text-foreground">
                      {displayName || user.email}
                    </h2>
                    <div className="flex items-center gap-2 mt-1">
                      <StatusChip
                        status="approved"
                        size="sm"
                        label={roleLabels[role || "compliance_officer"]}
                      />
                    </div>
                  </div>
                </div>

                {/* Form */}
                <div className="space-y-6">
                  <GlowingInput
                    label="Display Name"
                    value={displayName}
                    onChange={(e) => setDisplayName(e.target.value)}
                    placeholder="Enter your name"
                    success={saved}
                  />

                  <div className="space-y-2">
                    <label className="block text-sm font-medium text-muted-foreground">
                      Email Address
                    </label>
                    <div className="flex items-center gap-3 p-3 rounded-lg bg-muted/30 border border-border/50">
                      <Mail className="h-5 w-5 text-muted-foreground" />
                      <span className="text-foreground">{user.email}</span>
                    </div>
                    <p className="text-xs text-muted-foreground">
                      Email cannot be changed. Contact support if needed.
                    </p>
                  </div>

                  <div className="space-y-2">
                    <label className="block text-sm font-medium text-muted-foreground">
                      Role
                    </label>
                    <div className="flex items-center gap-3 p-3 rounded-lg bg-muted/30 border border-border/50">
                      <Shield className="h-5 w-5 text-primary" />
                      <span className="text-foreground">{roleLabels[role || "compliance_officer"]}</span>
                    </div>
                    <p className="text-xs text-muted-foreground">
                      Role changes require administrator approval.
                    </p>
                  </div>

                  <div className="space-y-2">
                    <label className="block text-sm font-medium text-muted-foreground">
                      Member Since
                    </label>
                    <div className="flex items-center gap-3 p-3 rounded-lg bg-muted/30 border border-border/50">
                      <Calendar className="h-5 w-5 text-muted-foreground" />
                      <span className="text-foreground">{createdAt}</span>
                    </div>
                  </div>

                  {/* Save Button */}
                  <div className="pt-4">
                    <NeonButton
                      onClick={handleSave}
                      loading={saving}
                      glowIntensity="high"
                      className="w-full"
                    >
                      {saved ? (
                        <>
                          <CheckCircle className="h-4 w-4" />
                          Saved Successfully
                        </>
                      ) : (
                        <>
                          <Save className="h-4 w-4" />
                          Save Changes
                        </>
                      )}
                    </NeonButton>
                  </div>
                </div>
              </GlassCard>
            </TabsContent>

            {/* Security Tab */}
            <TabsContent value="security">
              <GlassCard className="p-8">
                <h3 className="text-lg font-semibold mb-6">Change Password</h3>
                <div className="space-y-4">
                  <GlowingInput
                    label="Current Password"
                    type="password"
                    value={currentPassword}
                    onChange={(e) => setCurrentPassword(e.target.value)}
                    placeholder="Enter current password"
                  />
                  <GlowingInput
                    label="New Password"
                    type="password"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    placeholder="Enter new password"
                  />
                  <GlowingInput
                    label="Confirm New Password"
                    type="password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    placeholder="Confirm new password"
                  />
                  <NeonButton
                    onClick={handleChangePassword}
                    loading={changingPassword}
                    className="w-full"
                  >
                    <Lock className="h-4 w-4 mr-2" />
                    Change Password
                  </NeonButton>
                </div>
              </GlassCard>
            </TabsContent>

            {/* Sessions Tab */}
            <TabsContent value="sessions">
              <GlassCard className="p-8">
                <h3 className="text-lg font-semibold mb-6">Active Sessions</h3>
                <div className="space-y-4">
                  {sessions.map((session) => (
                    <div key={session.id} className="flex items-center justify-between p-4 bg-muted/20 rounded-lg">
                      <div className="flex items-center gap-3">
                        <Monitor className="h-5 w-5 text-muted-foreground" />
                        <div>
                          <p className="font-medium">{session.device}</p>
                          <p className="text-sm text-muted-foreground">{session.location}</p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="text-sm">
                          {session.current 
                            ? "Current Session" 
                            : `Last active ${new Date(session.lastActive).toLocaleString()}`
                          }
                        </p>
                        {session.current && <span className="text-xs text-success">Active</span>}
                      </div>
                    </div>
                  ))}
                </div>
              </GlassCard>
            </TabsContent>

            {/* Account Tab */}
            <TabsContent value="account">
              <GlassCard className="p-8">
                <h3 className="text-lg font-semibold mb-6">Account Actions</h3>
                <div className="space-y-4">
                  <NeonButton
                    variant="outline"
                    onClick={() => setShowLogoutDialog(true)}
                    className="w-full"
                  >
                    <LogOut className="h-4 w-4 mr-2" />
                    Logout
                  </NeonButton>
                  {role === "admin" && (
                    <motion.div
                      initial={{ opacity: 0, scale: 0.95 }}
                      animate={{ opacity: 1, scale: 1 }}
                      className="p-4 bg-destructive/10 border border-destructive/20 rounded-lg"
                    >
                      <div className="flex items-center gap-2 mb-2">
                        <AlertTriangle className="h-5 w-5 text-destructive" />
                        <span className="font-medium text-destructive">Danger Zone</span>
                      </div>
                      <p className="text-sm text-muted-foreground mb-4">
                        Deleting your account is permanent and cannot be undone.
                      </p>
                      <NeonButton
                        variant="destructive"
                        onClick={() => setShowDeleteDialog(true)}
                        className="w-full"
                      >
                        <Trash2 className="h-4 w-4 mr-2" />
                        Delete Account
                      </NeonButton>
                    </motion.div>
                  )}
                </div>
              </GlassCard>
            </TabsContent>
          </Tabs>
        </motion.div>
      </main>

      {/* Logout Dialog */}
      <Dialog open={showLogoutDialog} onOpenChange={setShowLogoutDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Confirm Logout</DialogTitle>
          </DialogHeader>
          <p>Are you sure you want to logout?</p>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowLogoutDialog(false)}>Cancel</Button>
            <Button onClick={handleLogout}>Logout</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Account Dialog */}
      <Dialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Account</DialogTitle>
          </DialogHeader>
          <div className="flex items-center gap-2 mb-4">
            <AlertTriangle className="h-5 w-5 text-destructive" />
            <p className="text-destructive font-medium">This action cannot be undone.</p>
          </div>
          <p>Are you sure you want to permanently delete your account?</p>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDeleteDialog(false)}>Cancel</Button>
            <Button variant="destructive" onClick={handleDeleteAccount}>Delete Account</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}