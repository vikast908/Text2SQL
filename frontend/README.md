# futureOS Text to SQL

## Project Overview

futureOS Text to SQL is a Text-to-SQL project that enables users to interact with databases using natural language queries.

## Getting Started

### Prerequisites

The only requirement is having Node.js & npm installed - [install with nvm](https://github.com/nvm-sh/nvm#installing-and-updating)

### Installation

Follow these steps to get the project running locally:

```sh
# Step 1: Clone the repository using the project's Git URL.
git clone <YOUR_GIT_URL>

# Step 2: Navigate to the project directory.
cd insight-navigator-53

# Step 3: Install the necessary dependencies.
npm i

# Step 4: Start the development server with auto-reloading and an instant preview.
npm run dev
```

## Development

### Available Scripts

- `npm run dev` - Start the development server
- `npm run build` - Build for production
- `npm run build:dev` - Build for development
- `npm run lint` - Run ESLint
- `npm run preview` - Preview the production build

### Editing the Code

You can edit the code using:

- **Your preferred IDE** - Clone the repo and work locally
- **GitHub** - Edit files directly in the GitHub web interface
- **GitHub Codespaces** - Use GitHub Codespaces for a cloud-based development environment

## Technologies

This project is built with:

- Vite
- TypeScript
- React
- shadcn-ui
- Tailwind CSS
- React Router
- TanStack Query

## Deployment

To deploy this project, you can use any static hosting service that supports Vite/React applications, such as:

- Vercel
- Netlify
- GitHub Pages
- AWS S3 + CloudFront
- Any other static hosting provider

Build the project using `npm run build` and deploy the `dist` folder to your hosting provider.
