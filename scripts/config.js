// =============================================
// SportsEdgeBet Configuration
// =============================================

const CONFIG = {
    // Supabase Configuration
    // Get these from: https://supabase.com/dashboard/project/YOUR_PROJECT/settings/api
    SUPABASE_URL: 'https://oecotvkdpgpmcgfcfjap.supabase.co', // e.g., 'https://oecotvkdpgpmcgfcfjap.supabase.co'
    SUPABASE_ANON_KEY: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9lY290dmtkcGdwbWNnZmNmamFwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njc3MTgyNzEsImV4cCI6MjA4MzI5NDI3MX0.glPXyCdiiEx7_KaCojAtnM9rlGj03IIj2AGirF6tAy8',
    
    // Stripe Configuration  
    // Get these from: https://dashboard.stripe.com/apikeys
    STRIPE_PUBLISHABLE_KEY: 'YOUR_STRIPE_PUBLISHABLE_KEY', // pk_test_... or pk_live_...
    
    // Stripe Price IDs (create these in Stripe Dashboard > Products)
    STRIPE_PRICES: {
        pro_monthly: 'price_xxxxx', // $29/month
        pro_yearly: 'price_xxxxx',  // $276/year (save 20%)
        elite_monthly: 'price_xxxxx', // $79/month
        elite_yearly: 'price_xxxxx'   // $758/year (save 20%)
    },
    
    // App Configuration
    APP_URL: 'https://sportsedgebet.com',
    
    // Subscription Plans
    PLANS: {
        free: {
            name: 'Starter',
            price: 0,
            features: [
                'Basic odds comparison',
                '5 sportsbooks',
                'Major sports only',
                '15-min delayed odds'
            ]
        },
        pro: {
            name: 'Pro',
            price: 29,
            yearlyPrice: 23,
            features: [
                'Real-time odds comparison',
                'All 30+ sportsbooks',
                'All sports & leagues',
                'Instant line alerts',
                'Value bet finder',
                'Bet tracker'
            ]
        },
        elite: {
            name: 'Elite',
            price: 79,
            yearlyPrice: 63,
            features: [
                'Everything in Pro',
                'Arbitrage alerts',
                'Expert handicapper picks',
                'API access',
                'Priority support',
                'Early access to features'
            ]
        }
    },
    
    // Affiliate Configuration
    AFFILIATE: {
        defaultCommission: 20, // 20%
        cookieDays: 30, // Cookie lasts 30 days
        minPayout: 50 // Minimum $50 to request payout
    }
};

// Don't modify below this line
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CONFIG;
}


