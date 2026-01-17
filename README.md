# SportsEdgeBet - Sports Betting Odds Comparison Platform

A modern, responsive website for comparing sports betting odds across multiple sportsbooks. Features a subscription model with free trial, designed to help bettors find the best odds and maximize value.

![SportsEdgeBet Preview](https://via.placeholder.com/1200x600/0a0a0b/22c55e?text=SportsEdgeBet)

## 🚀 Features

### For Users
- **Real-time Odds Comparison** - Compare odds from 30+ sportsbooks instantly
- **Best Odds Highlighting** - Automatically identifies the best available odds
- **Value Bet Finder** - AI-powered tool to find mispriced lines
- **Line Movement Alerts** - Get notified when odds shift in your favor
- **Bet Tracker** - Log and track all your bets in one place
- **Arbitrage Detection** - Find guaranteed profit opportunities (Elite plan)
- **All Sports Coverage** - NFL, NBA, MLB, NHL, Soccer, Tennis, MMA, Golf, and more

### Subscription Tiers

| Feature | Starter (Free) | Pro ($29/mo) | Elite ($79/mo) |
|---------|---------------|--------------|----------------|
| Sportsbooks | 5 | 30+ | 30+ |
| Sports | Major US only | All | All |
| Odds Speed | 15 min delay | Real-time | Real-time |
| Line Alerts | ❌ | ✅ | ✅ |
| Value Finder | ❌ | ✅ | ✅ |
| Bet Tracking | ❌ | ✅ | ✅ |
| Arbitrage Alerts | ❌ | ❌ | ✅ |
| Expert Picks | ❌ | ❌ | ✅ |
| API Access | ❌ | ❌ | ✅ |

### Trial Model
- **7-Day Free Trial** for Pro and Elite tiers
- No credit card required to start
- Full access to all features during trial
- Automatic downgrade to Starter if not converted
- 30-day money-back guarantee after payment

## 📁 Project Structure

```
sportsedgebet/
├── index.html          # Landing page with features, pricing, testimonials
├── dashboard.html      # Main odds comparison dashboard
├── pricing.html        # Detailed pricing page with comparison table
├── styles/
│   └── main.css        # All styles (variables, components, responsive)
├── scripts/
│   └── main.js         # Interactivity, animations, modals
└── README.md           # This file
```

## 🎨 Design System

### Colors
- **Background**: Deep black (#0a0a0b) with subtle grays
- **Accent**: Electric green (#22c55e) for CTAs and highlights
- **Positive**: Green for winning odds and increases
- **Negative**: Red for losses and decreases

### Typography
- **Primary Font**: Outfit (modern, clean sans-serif)
- **Monospace Font**: Space Mono (for odds and numbers)

### Components
- Cards with subtle borders and hover effects
- Glowing primary buttons
- Smooth animations and transitions
- Responsive grid layouts

## 🛠️ Getting Started

### Prerequisites
- A modern web browser
- A local development server (optional, for best results)

### Installation

1. Clone or download the repository:
```bash
git clone https://github.com/yourusername/sportsedgebet.git
cd sportsedgebet
```

2. Open in browser:
   - Simply open `index.html` in your browser, or
   - Use a local server for best results:

```bash
# Using Python
python -m http.server 8000

# Using Node.js (npx)
npx serve

# Using PHP
php -S localhost:8000
```

3. Visit `http://localhost:8000` in your browser

## 📱 Pages

### Landing Page (`index.html`)
- Hero section with animated floating odds cards
- Feature showcase with highlighted "Real-time Odds" card
- How it works - 3-step process
- Pricing preview with monthly/yearly toggle
- Testimonials from users
- FAQ accordion
- Call-to-action section

### Dashboard (`dashboard.html`)
- Sidebar navigation
- Trial countdown banner
- Statistics cards
- Sport category tabs
- Live games with odds comparison
- Upcoming games list
- Best odds highlighting
- Arbitrage opportunity badges

### Pricing Page (`pricing.html`)
- Detailed plan comparison cards
- Monthly/yearly billing toggle
- Feature comparison table
- Trial information cards
- Money-back guarantee section
- Pricing-specific FAQ

## 🔧 Customization

### Changing Colors
Edit the CSS variables in `styles/main.css`:

```css
:root {
    --accent-primary: #22c55e;      /* Main green */
    --accent-secondary: #10b981;    /* Secondary green */
    --bg-primary: #0a0a0b;          /* Main background */
    --bg-card: #1a1a1d;             /* Card background */
    /* ... more variables */
}
```

### Adding New Sports
In `dashboard.html`, add a new tab:

```html
<button class="sport-tab">
    🏏 Cricket
    <span class="count">15</span>
</button>
```

### Adding New Sportsbooks
Add to the comparison display and update the logos section in `index.html`.

## 🚀 Deployment

This is a static site that can be deployed anywhere:

- **Netlify**: Drag & drop the folder
- **Vercel**: `npx vercel`
- **GitHub Pages**: Push to `gh-pages` branch
- **AWS S3**: Upload files to bucket with static hosting

## 📈 Future Enhancements

- [ ] Backend API integration for real odds data
- [ ] User authentication system
- [ ] Stripe payment integration
- [ ] Mobile app (React Native)
- [ ] Push notifications for alerts
- [ ] Historical odds data and charts
- [ ] Social features (share bets, leaderboards)
- [ ] Dark/light theme toggle

## 📄 License

MIT License - feel free to use this for your own projects.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

Built with ❤️ for sports bettors who want an edge.


