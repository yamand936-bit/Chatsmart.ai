# ChatSmart AI - MASTER BLUEPRINT

<div dir="rtl" style="text-align: right;">

## مقدمة
مرحباً بك في الوثيقة الهندسية الشاملة لمنصة **ChatSmart AI**. 
تم إعداد هذا الدليل ليكون "المرجع الذهبي" الذي يوثّق كافة تفاصيل البنية التحتية، التقنيات المستخدمة، منطق الذكاء الاصطناعي، والمسار التطويري الذي سلكناه وصولاً إلى المرحلة العاشرة. يهدف هذا التقرير إلى تمكين أي مهندس برمجيات (Senior Developer) من فهم النظام المعقد واستيعاب كافة الارتباطات بين الواجهة الأمامية، الخوادم الخلفية، وقواعد البيانات، بحيث يمكنه تطوير، صيانة، أو حتى إطلاق منصة مطابقة بسلاسة تامة.

</div>

---

## 1. High-Level Architecture
ChatSmart AI is built upon a scalable, production-ready microservices architecture utilizing isolated containers, async protocols, and modern framework ecosystems:
- **Backend (FastAPI & Python 3.10+):** The core engine of the system. Implemented with asynchronous routing to handle high-concurrency requests, websocket streaming, and demanding background tasks (like AI request processing and Webhooks).
- **Frontend (Next.js 14):** A highly responsive App Router-based structure. Uses Server-Side Rendering (SSR) where applicable, and robust Client Components for real-time reactivity, fully supporting internationalization (i18n).
- **Caching & Brokers (Redis):** Orchestrates transient context caches, rate limiting, token buckets, and manages distributed tasks between the app and the background Celery workers (used in advanced deployments).
- **Reverse Proxy & SSL (Nginx):** Positioned upstream to handle direct client connections (HTTPS/443). It terminates SSL certificates (via Certbot/Let's Encrypt), dynamically proxies requests to Next.js (`:3000`) for the dashboard UI, and natively routes `/api` and `/webhook` requests directly to FastAPI (`:8000`).
- **Containerization (Docker Compose):** Simplifies environment replication, securely networking `db`, `redis`, `api`, and `web` under a unified isolated network.

## 2. Database & Data Modeling (PostgreSQL)
The application utilizes **PostgreSQL 15** acting as the resilient single source of truth, heavily relying on SQLAlchemy ORM and Alembic migrations.

### Key Entities
| Entity | Description & Primary Relations |
| --- | --- |
| **Business/Merchant** | Tracks distinct SaaS tenants. Holds unique keys (`bot_token`, API keys), token consumption limits, metadata, and preferred AI models. |
| **Customer** | Distinct user profiles uniquely matched per `business_id` and `platform_id` (e.g., WhatsApp Number). <br/>**[Advanced]** Includes `tags` (JSON) automatically assigned by AI intent analysis. |
| **Conversation & Message** | Retains all interactions. <br/>**[Advanced]** The `Message` table features a `response_time` (Float) column to power the Admin Performance tracking. |
| **Products & Orders** | The E-commerce logic representing the merchant's live catalog arrays. Connected to Excel sync updates. |
| **SystemErrorLog** | A vital repository capturing `error_type` and `message` to alert Super Admins of failing webhooks, token expiries, or integration faults. |
| **Campaigns [Phase 10]** | Tracks out-reach status. A specialized column maps AI personalized bulk messages. |

## 3. AI Engine & Multimodal Logic
The system's intelligence goes beyond simple chat bindings, leveraging advanced chained operations via **LangChain** and direct API access to frontier models (**GPT-4o**, **Gemini 1.5 Pro**, **Claude 3.5 Sonnet**).

- **Full Context Memory (Zero Limits):** ChatSmart fundamentally refuses to truncate historical chat vectors. The raw database retrieval fetches all unified histories into the completion context, ensuring absolute persistency and hyper-personalized interaction. 
- **Audio Processing (Voice AI):** Incoming WhatsApp/Telegram `.ogg` or `.mp3` payloads trigger local background tasks. The Webhook fetches the media using Meta Graph API, stores it temporarily, formats it, and invokes **OpenAI Whisper**. The extracted transcription dynamically feeds into the standard text-pipeline.
- **Computer Vision (Image Analysis):** Routers are injected with dynamic multimodal capability. If an incoming message object contains a media url matching image mimetypes (`.jpg`, `.png`), the underlying `ai_engine.py` dynamically escalates the request specifically to `gpt-4o` (or `gemini-1.5-pro-vision`) to explicitly provide object analysis or read receipt validations.

## 4. Advanced Functional Modules
### Excel Sync Engine
A seamless ingestion pipeline that parses uploaded `xlsx` arrays or pulls directly from a provided Google Sheets URL using `pandas`. This logic creates, updates, and maps items safely to the `Products` table, avoiding duplicates through strict primary-key heuristics.

### Smart Campaigns & Auto-Tagging CRM (Phase 10)
Instead of static tags, we utilize **AI Auto-Tagging**:
1. Post-chat, a background task reads the dialogue and extrapolates latent intent.
2. The AI returns precise descriptive labels (e.g., `Purchased-Perfume`, `Hesitant`).
3. Using the **Smart Campaigns Manager**, merchants can define a broadcast target tag. The framework loops through matched customers, loads their unique history, and forces the LLM to write a *bespoke* message taking prior references into account before transmitting sequentially.

### Admin Center Intelligence
A robust Super Admin environment devoid of basic metrics. It calculates "Effective Cost" versus "Expected Profit" per AI Token. The platform explicitly measures absolute latency (`Avg Response Time`) via database tracking, highlighting degraded logic automatically in the root dashboard if latency >5s.

## 5. Localization & UI Structure
The entire SAAS ecosystem natively supports **Arithmetic RTL / LTR dynamically**:
- **Languages Supported:** Arabic (AR), English (EN), Turkish (TR).
- **Framework:** Leverages `next-intl`. 
- **Implementation:** Translation JSONs (`ar.json`, `en.json`, `tr.json`) handle over +300 distinct UI keys. Text sizes, flex alignments, and absolute positioning seamlessly pivot based on the HTML `dir` attribute assigned in the root `app/layout.tsx`. Admin components dynamically map AI model names based on active dialect to avoid cognitive dissonance.

## 6. Deployment & DevOps Strategy
ChatSmart AI is tuned for a VPS Linux environment (e.g., Contabo).

### `docker-compose.yml` Pipeline
The deployment strictly isolates roles:
- `db` & `redis` expose internal ports securely using health-checks.
- `api` is rebuilt using `./backend/Dockerfile` with `poetry` or `requirements.txt`.
- `web` uses a multi-stage Next.js builder, outputting a highly optimized standalone module mapped to port 3000.

### Barebone Operations Guide
```bash
# 1. Project Setup
git pull origin main
cd chatsmartai
cp backend/.env.example backend/.env # ensure OPENAI_API_KEY, JWT_SECRET, etc. are set

# 2. Build Ecosystem
docker-compose up -d --build

# 3. Database Migration (Execute strictly inside the api container)
docker exec -it chatsmart_api alembic upgrade head

# 4. View Runtime Logs
docker compose logs -f api
```
*Note: Ensure Nginx is configured on the host machine mapping rules to ProxyPass `/` to `http://localhost:3000` and `/api/` to `http://localhost:8000`.*

## 7. Development Roadmap Summary (Phases 1-10)
- **Phase 1-3:** Foundation. SQLite to Postgres migration. FastAPI basic endpoints. Next.js structure formulation.
- **Phase 4-5:** Authentication & Auth-Guards. Setup robust JWT issuing, refreshing, HTTP-only cookies, and multi-tenant logic ensuring merchants can only access their specific `business_id` assets.
- **Phase 6:** i18n Internationalization. Massive restructuring of hardcoded strings to uniform Translation Files spanning all Admin & Merchant UIs.
- **Phase 7:** Docker Compose containerization and Contabo Deployment prep. SSL setup overview.
- **Phase 8-9:** Super Admin Dashboards, Token monitoring logic, Impersonation (Login as Merchant), Error Logs, and Dynamic Routing fixes for Nginx 422 errors.
- **Phase 10:** AI Sales Mastery. Implemented Whisper Audio Transcriptions, GPT-4o Vision API, Seamless Asynchronous CRM Tagging, and the Smart Campaign Architect.

---

<div dir="rtl" style="text-align: right;">

## خاتمة
بوصولنا إلى هذه المرحلة، لم يعد ChatSmart AI مجرد بوت محادثة، بل تحوّل إلى إطار عمل تسويقي ومؤسسي لامركزي ومحطة إدارة شاملة للذكاء الاصطناعي متعدد الأبعاد. سواء كان التحدي هو مراقبة التكاليف الميكرو-سنتية لطلبات الذكاء، أو تسويق حملة بآلاف الرسائل الصوتية والنصية بالاعتماد على سياقات الزبائن؛ فإن هذا المشروع مهيأ ومبني ليكون في صدارة أنظمة الـ SaaS عالمياً.
شكراً لك على ثقتك، ومبارك لنا ولكم هذا الإنجاز التقني العملاق!

</div>
