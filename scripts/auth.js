// =============================================
// SportsEdgeBet Authentication Module
// =============================================

// Initialize Supabase client
const supabase = window.supabase.createClient(CONFIG.SUPABASE_URL, CONFIG.SUPABASE_ANON_KEY);

// =============================================
// Authentication Functions
// =============================================

const Auth = {
    // Get current user
    async getCurrentUser() {
        const { data: { user }, error } = await supabase.auth.getUser();
        if (error) {
            console.error('Error getting user:', error);
            return null;
        }
        return user;
    },

    // Get current session
    async getSession() {
        const { data: { session }, error } = await supabase.auth.getSession();
        if (error) {
            console.error('Error getting session:', error);
            return null;
        }
        return session;
    },

    // Sign up with email and password
    async signUp(email, password, fullName = '') {
        const { data, error } = await supabase.auth.signUp({
            email,
            password,
            options: {
                data: {
                    full_name: fullName
                },
                emailRedirectTo: `${CONFIG.APP_URL}/account.html`
            }
        });

        if (error) {
            throw error;
        }

        // Check for referral code in cookie and track it
        const refCode = getCookie('ref');
        if (refCode && data.user) {
            await this.trackReferral(data.user.id, refCode);
        }

        return data;
    },

    // Sign in with email and password
    async signIn(email, password) {
        const { data, error } = await supabase.auth.signInWithPassword({
            email,
            password
        });

        if (error) {
            throw error;
        }

        return data;
    },

    // Sign in with OAuth (Google, GitHub, etc.)
    async signInWithOAuth(provider) {
        const { data, error } = await supabase.auth.signInWithOAuth({
            provider,
            options: {
                redirectTo: `${CONFIG.APP_URL}/account.html`
            }
        });

        if (error) {
            throw error;
        }

        return data;
    },

    // Sign out
    async signOut() {
        const { error } = await supabase.auth.signOut();
        if (error) {
            throw error;
        }
        window.location.href = '/index.html';
    },

    // Reset password
    async resetPassword(email) {
        const { data, error } = await supabase.auth.resetPasswordForEmail(email, {
            redirectTo: `${CONFIG.APP_URL}/reset-password.html`
        });

        if (error) {
            throw error;
        }

        return data;
    },

    // Update password
    async updatePassword(newPassword) {
        const { data, error } = await supabase.auth.updateUser({
            password: newPassword
        });

        if (error) {
            throw error;
        }

        return data;
    },

    // Update user profile
    async updateProfile(updates) {
        const user = await this.getCurrentUser();
        if (!user) throw new Error('Not authenticated');

        const { data, error } = await supabase
            .from('profiles')
            .update(updates)
            .eq('id', user.id)
            .select()
            .single();

        if (error) {
            throw error;
        }

        return data;
    },

    // Get user profile with subscription
    async getProfile() {
        const user = await this.getCurrentUser();
        if (!user) return null;

        const { data, error } = await supabase
            .from('profiles')
            .select(`
                *,
                subscriptions (*),
                affiliates (*)
            `)
            .eq('id', user.id)
            .single();

        if (error) {
            console.error('Error fetching profile:', error);
            return null;
        }

        return data;
    },

    // Track referral
    async trackReferral(userId, affiliateCode) {
        try {
            // Find affiliate by code
            const { data: affiliate } = await supabase
                .from('affiliates')
                .select('id')
                .eq('affiliate_code', affiliateCode)
                .single();

            if (affiliate) {
                // Create referral record
                await supabase
                    .from('referrals')
                    .insert({
                        affiliate_id: affiliate.id,
                        referred_user_id: userId
                    });
            }
        } catch (error) {
            console.error('Error tracking referral:', error);
        }
    },

    // Listen for auth state changes
    onAuthStateChange(callback) {
        return supabase.auth.onAuthStateChange((event, session) => {
            callback(event, session);
        });
    },

    // Check if user is authenticated
    async isAuthenticated() {
        const user = await this.getCurrentUser();
        return !!user;
    },

    // Require authentication (redirect if not logged in)
    async requireAuth() {
        const isAuth = await this.isAuthenticated();
        if (!isAuth) {
            window.location.href = '/login.html?redirect=' + encodeURIComponent(window.location.pathname);
            return false;
        }
        return true;
    }
};

// =============================================
// Subscription Functions
// =============================================

const Subscription = {
    // Get user's subscription
    async get() {
        const user = await Auth.getCurrentUser();
        if (!user) return null;

        const { data, error } = await supabase
            .from('subscriptions')
            .select('*')
            .eq('user_id', user.id)
            .single();

        if (error) {
            console.error('Error fetching subscription:', error);
            return null;
        }

        return data;
    },

    // Check if user has active paid subscription
    async isPaid() {
        const sub = await this.get();
        return sub && (sub.plan_id === 'pro' || sub.plan_id === 'elite') && sub.status === 'active';
    },

    // Get plan details
    getPlanDetails(planId) {
        return CONFIG.PLANS[planId] || CONFIG.PLANS.free;
    }
};

// =============================================
// Affiliate Functions
// =============================================

const Affiliate = {
    // Become an affiliate
    async becomeAffiliate() {
        const { data, error } = await supabase.rpc('become_affiliate');
        
        if (error) {
            throw error;
        }

        return data;
    },

    // Get affiliate data
    async get() {
        const user = await Auth.getCurrentUser();
        if (!user) return null;

        const { data, error } = await supabase
            .from('affiliates')
            .select(`
                *,
                referrals (*)
            `)
            .eq('user_id', user.id)
            .single();

        if (error && error.code !== 'PGRST116') {
            console.error('Error fetching affiliate:', error);
        }

        return data;
    },

    // Get affiliate stats
    async getStats() {
        const affiliate = await this.get();
        if (!affiliate) return null;

        const totalReferrals = affiliate.referrals?.length || 0;
        const convertedReferrals = affiliate.referrals?.filter(r => r.status === 'converted').length || 0;

        return {
            affiliateCode: affiliate.affiliate_code,
            referralLink: `${CONFIG.APP_URL}?ref=${affiliate.affiliate_code}`,
            totalReferrals,
            convertedReferrals,
            conversionRate: totalReferrals > 0 ? (convertedReferrals / totalReferrals * 100).toFixed(1) : 0,
            totalEarnings: affiliate.total_earnings,
            pendingEarnings: affiliate.pending_earnings,
            paidEarnings: affiliate.paid_earnings,
            commissionRate: affiliate.commission_rate
        };
    },

    // Update payout info
    async updatePayoutInfo(paypalEmail) {
        const user = await Auth.getCurrentUser();
        if (!user) throw new Error('Not authenticated');

        const { data, error } = await supabase
            .from('affiliates')
            .update({ paypal_email: paypalEmail })
            .eq('user_id', user.id)
            .select()
            .single();

        if (error) {
            throw error;
        }

        return data;
    }
};

// =============================================
// Utility Functions
// =============================================

// Cookie utilities for referral tracking
function setCookie(name, value, days) {
    const expires = new Date();
    expires.setTime(expires.getTime() + days * 24 * 60 * 60 * 1000);
    document.cookie = `${name}=${value};expires=${expires.toUTCString()};path=/`;
}

function getCookie(name) {
    const nameEQ = name + '=';
    const ca = document.cookie.split(';');
    for (let i = 0; i < ca.length; i++) {
        let c = ca[i];
        while (c.charAt(0) === ' ') c = c.substring(1, c.length);
        if (c.indexOf(nameEQ) === 0) return c.substring(nameEQ.length, c.length);
    }
    return null;
}

// Check for referral code in URL
function checkReferralCode() {
    const urlParams = new URLSearchParams(window.location.search);
    const refCode = urlParams.get('ref');
    if (refCode) {
        setCookie('ref', refCode, CONFIG.AFFILIATE.cookieDays);
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    checkReferralCode();
});

// =============================================
// UI Helper Functions
// =============================================

const UI = {
    // Show loading state
    showLoading(button) {
        button.disabled = true;
        button.dataset.originalText = button.innerHTML;
        button.innerHTML = '<span class="spinner"></span> Loading...';
    },

    // Hide loading state
    hideLoading(button) {
        button.disabled = false;
        button.innerHTML = button.dataset.originalText;
    },

    // Show error message
    showError(container, message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.textContent = message;
        
        // Remove existing error
        const existing = container.querySelector('.error-message');
        if (existing) existing.remove();
        
        container.insertBefore(errorDiv, container.firstChild);
        
        // Auto-remove after 5 seconds
        setTimeout(() => errorDiv.remove(), 5000);
    },

    // Show success message
    showSuccess(container, message) {
        const successDiv = document.createElement('div');
        successDiv.className = 'success-message';
        successDiv.textContent = message;
        
        // Remove existing success
        const existing = container.querySelector('.success-message');
        if (existing) existing.remove();
        
        container.insertBefore(successDiv, container.firstChild);
        
        // Auto-remove after 5 seconds
        setTimeout(() => successDiv.remove(), 5000);
    },

    // Update navigation based on auth state
    async updateNav() {
        const user = await Auth.getCurrentUser();
        const navActions = document.querySelector('.nav-actions');
        
        if (navActions) {
            if (user) {
                navActions.innerHTML = `
                    <a href="/account.html" class="btn btn-ghost">Account</a>
                    <button onclick="Auth.signOut()" class="btn btn-outline">Logout</button>
                `;
            } else {
                navActions.innerHTML = `
                    <a href="/login.html" class="btn btn-ghost">Login</a>
                    <a href="/signup.html" class="btn btn-primary">Sign Up</a>
                `;
            }
        }
    }
};


