










import os
from dotenv import load_dotenv

load_dotenv()

# ── Required ──────────────────────────────────────────────────────────────────
BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")

# ── Database ──────────────────────────────────────────────────────────────────
DB_PATH: str = os.getenv("DB_PATH", "data/jobot.db")


# ── Role categories shown on /subscribe ───────────────────────────────────────
# These appear as tap-to-pick buttons in the subscribe flow.
# Categories are shown as headers, roles as buttons.
ROLE_CATEGORIES: dict = {
    "Frontend": [
        "Frontend Developer",
        "React Developer",
        "Vue Developer",
        "Angular Developer",
        "Next.js Developer",
        "UI Developer",
        "JavaScript Developer",
        "TypeScript Developer",
    ],
    "Backend": [
        "Backend Developer",
        "Node.js Developer",
        "Python Developer",
        "Django Developer",
        "FastAPI Developer",
        "PHP Developer",
        "Java Developer",
        "Go Developer",
    ],
    "Full Stack": [
        "Full Stack Developer",
        "Full Stack Engineer",
        "MERN Stack Developer",
        "MEAN Stack Developer",
    ],
    "DevOps / Cloud": [
        "DevOps Engineer",
        "Cloud Engineer",
        "AWS Engineer",
        "Platform Engineer",
        "Site Reliability Engineer",
        "Infrastructure Engineer",
        "CI/CD Engineer",
    ],
    "Systems / Linux": [
        "Linux Administrator",
        "System Administrator",
        "Linux Engineer",
        "Network Engineer",
        "IT Administrator",
        "Unix Administrator",
        "Windows Administrator",
    ],
    "Software Engineering": [
        "Software Engineer",
        "Software Developer",
        "Mobile Developer",
        "iOS Developer",
        "Android Developer",
    ],
}

# ── Target job roles ──────────────────────────────────────────────────────────
TARGET_ROLES = [
    # Frontend
    "frontend", "front-end", "front end",
    "react", "vue", "angular", "nextjs", "next.js", "svelte",
    "javascript", "typescript", "html", "css", "tailwind", "framer",
    # Backend
    "backend", "back-end", "back end",
    "node", "nodejs", "python", "django", "fastapi", "flask",
    "java", "spring", "php", "laravel", "ruby", "rails", "golang",
    # Full Stack
    "full stack", "fullstack", "full-stack",
    # DevOps / Cloud / Infrastructure
    "devops", "dev ops",
    "cloud engineer", "cloud architect", "cloud administrator",
    "aws", "gcp", "azure", "google cloud",
    "kubernetes", "k8s", "docker", "terraform", "ansible", "puppet", "chef",
    "ci/cd", "gitlab ci", "github actions", "jenkins",
    "sre", "site reliability", "platform engineer", "platform engineering",
    "devsecops", "secops",
    "infrastructure engineer", "infrastructure as code", "iac",
    "network engineer", "network administrator",
    # System Administration / Linux
    "sysadmin", "sys admin", "system administrator", "systems administrator",
    "system admin", "systems admin",
    "linux administrator", "linux admin", "linux engineer",
    "linux", "ubuntu", "debian", "centos", "rhel", "red hat",
    "unix", "unix administrator",
    "windows administrator", "windows admin", "active directory",
    "server administrator", "server admin",
    "it administrator", "it admin", "it support", "it engineer",
    "helpdesk", "help desk", "technical support", "tech support",
    "bash", "shell scripting", "powershell",
    "virtualization", "vmware", "hyper-v",
    "storage engineer", "backup engineer", "disaster recovery",
    # General
    "software engineer", "software developer", "developer", "engineer",
]

# ── Location filter ───────────────────────────────────────────────────────────
REMOTE_ONLY: bool = True

# ── Reddit subreddits (all from your list) ────────────────────────────────────
REDDIT_SUBREDDITS = [
    # ── Dev / Tech jobs ───────────────────────────────────────────────────────
    "forhire",
    "forhire2",
    "ForHireFreelance",
    "DeveloperJobs",
    "developers_hire",
    "developers",
    "developer",
    "dev",
    "DeveloperAIjobs",
    "ExperiencedDevs",
    "FullStackDevelopers",
    "CodingJobs",
    "coding",
    "WebDeveloperJobs",
    "WebDevJobs",
    "webdevelopment",
    "webdev",
    "web_design",
    "webdesign",
    "websiteservices",
    "frontend",
    "reactjs",
    "vuejs",
    "javascript",
    "learnjavascript",
    "learnprogramming",
    "learnpython",
    "programming",
    "softwaredevelopment",
    "hireaideveloper",
    "AppDevelopers",
    "AppBuilding",
    # ── Remote / freelance jobs ───────────────────────────────────────────────
    "remotejs",
    "RemoteJobs",
    "remotejobsdaily",
    "RemoteJobseekers",
    "remotejobsfinders",
    "RemoteJobsSearch",
    "remotepython",
    "remotework",
    "RemoteWorkers",
    "remoteworking",
    "WFHJobs",
    "WorkAtHomeOnline",
    "WorkOnline",
    "WorkOnlineJobs",
    "PaidOnlineJobs",
    "GetEmployed",
    "searchjob",
    "jobbit",
    "jobs",
    "hiring",
    "hiringhelp",
    "HiringPH",
    "cscareerquestions",
    "ITCareerQuestions",
    "careerguidance",
    "CareerSuccess",
    "interviews",
    # ── Freelance ─────────────────────────────────────────────────────────────
    "freelance",
    "freelance_forhire",
    "FreelanceProgramming",
    "freelancer_hire",
    "Freelancers",
    "freelancing",
    # ── Design ────────────────────────────────────────────────────────────────
    "UI_Design",
    "graphic_design",
    "GraphicDesigning",
    "GraphicDesignJobs",
    "GraphicDesignServices",
    "Designers_forhire",
    "DesignJobs",
    # ── Kenya / Africa focused ────────────────────────────────────────────────
    "Kenya",
    "nairobi",
    "nairobitechies",
    "Majuu254",
    "Opportunities_Kenya",
    "JobsKenyaHub",
    "marketplacekenya",
    "SellAnythingKe",
    "Eldoret",
    # ── Cloud / DevOps ────────────────────────────────────────────────────────
    "Cloud",
    "cloudengineering",
    "microservices",
    # ── AI / Data ─────────────────────────────────────────────────────────────
    "AIJobs",
    "AiAutomations",
    "AiBuilders",
    "AISaaSHunter",
    "outlier_ai",
    "datascience",
    "datasciencecareers",
    "DataScienceJobs",
    "datasciencenews",
    "DataAnnotationTech",
    "BigDataJobs",
    # ── Startup / business ────────────────────────────────────────────────────
    "Startup_Ideas",
    "smallbusiness",
    "smallbusinessesowners",
    "BusinessDevelopment",
    "SaaS",
    "SaasDevelopers",
    "B2BForHire",
    # ── Other job boards ──────────────────────────────────────────────────────
    "gigs_hiring",
    "HireVirtualAssistants",
    "techfreshers",
    "Upwork",
    "JobPH",
    "JobBit",
    "RecruitingHiringPH",
    "LatAmCoders",
    "PinoyProgrammer",
    "slavelabour",
    "DoneDirtCheap",
    "beermoney",
    "beercash",
    "beermoneyglobal",
]

# ── RSS feeds ─────────────────────────────────────────────────────────────────
RSS_FEEDS: list[str] = [
    # We Work Remotely
    "https://weworkremotely.com/remote-jobs.rss",
    # Remotive
    "https://remotive.com/remote-jobs/feed",
    # Stack Overflow
    "https://stackoverflow.com/jobs/feed?r=true",
    # NoDesk — curated remote jobs
    "https://nodesk.co/remote-jobs/feed/",
    # Monster — role-specific remote searches
    "https://feeds.monster.com/rss/search?q=remote+software+developer&where=remote",
    "https://feeds.monster.com/rss/search?q=remote+frontend+developer&where=remote",
    "https://feeds.monster.com/rss/search?q=remote+devops+engineer&where=remote",
    "https://feeds.monster.com/rss/search?q=remote+linux+administrator&where=remote",
]

# ── Behaviour ─────────────────────────────────────────────────────────────────
FETCH_INTERVAL_MINUTES: int = int(os.getenv("FETCH_INTERVAL_MINUTES", "10"))
MAX_JOBS_PER_MESSAGE: int = 5

# ── Server ────────────────────────────────────────────────────────────────────
PORT: int = int(os.getenv("PORT", "8080"))