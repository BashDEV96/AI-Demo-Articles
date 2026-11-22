# Stop Writing Sixty Articles By Hand

So you bought a WordPress theme. Big dreams, magazine front page, a whole demo that looked like a money printer with a login screen.

You imported the demo and your new site filled up with dozens of articles and cool pictures, exactly like they promised. Then you started reading. Every article is Lorem Ipsum, or a mashup of movie lines, or whatever nonsense the theme developer thought was funny at 2 a.m. in the morning.

**Congratulations. You now have sixty articles to write.**

This little program fixes that. It reads each post title on your site, asks an AI to write a real article for it, and swaps the placeholder text for the new article. No plugin, no monthly subscription, no word spinner.

## Why this works

The theme gave you a shell: dozens of posts with real titles and fake bodies. The titles are useful. The bodies are garbage. All you need is something that reads each title and writes a real article to replace the fake one.

That is not a content empire. That is a loop.

1. **Read the title.** The program logs into your site and pulls each post. It ignores the body, since that is what we are replacing.
2. **Write the replacement.** The title goes to the AI along with the instructions in `Prompts/article.md`: headings, lists, a table if it fits, bold and italic where they help.
3. **Replace the garbage.** The program saves a backup of the original, posts the new article in its place, and moves to the next one.

Full disclosure: the output will not win a Pulitzer. It will be readable, structured, and on topic, which is a massive upgrade from placeholder text.

## What this is not

Let's be clear about what we are doing here. This is **not** an "SEO content silo writing empire." There is no keyword research, no topic clusters, no internal linking strategy, no ranking plan, and no secret formula for page one of Google. If you came looking for a money printer, the theme demo already promised you one of those, and look how that went.

What this *is* is a boring, honest fix for a common, annoying problem: you have a pile of fake articles and no desire to write sixty real ones just to make your new site stop looking like a theme demo.

Here is what the program does **not** do:

- **It does not research anything.** It sees a title and writes from whatever the AI already knows. It can be wrong, vague, or confidently make things up, so do not treat the articles as expert advice and do not publish anything you would be embarrassed to defend.
- **It does not do SEO.** No keywords, no meta descriptions, no clever structure for search engines. The articles are just readable and on topic.
- **It does not make images.** Your theme's demo pictures stay exactly as they are with an exception of inline images. They get deleted as well.
- **It does not touch your pages, menus, or categories.** Only the body text of your posts changes.
- **It does not make your site good.** It makes your site stop being full of Lorem Ipsum. Making it actually good is still your job, and it is a fun one once the garbage is gone.
- **It does not make money.** It saves you thirty bucks and a weekend. That is the whole pitch.

If someday you want to write real, researched, strategic content, this will be a nice placeholder-killer to have used first. Until then, we are just taking out the trash.

## What you need

Nothing expensive.

- **A computer with Python 3.** This was built and tested on Linux Mint.
- **A WordPress site with HTTPS.** Application passwords only work over HTTPS.You can use HTTP sites with a workaround - Google it.
- **A WordPress application password.** This lets the program log in without your real password. In WordPress, go to *Users > Profile*, scroll to **Application Passwords**, type a name (anything, like "rewriter"), and click **Add New Application Password**. Copy it somewhere safe, because WordPress will not show it again.
- **An AI key.** Some options are free:

| Provider | Where to get a key | Cost |
|---|---|---|
| Google AI Studio (`google`) | aistudio.google.com | free tier available |
| OpenRouter (`openrouter`) | openrouter.ai | free models plus paid ones |
| OpenAI (`openai`) | platform.openai.com | paid |

## Setup

Put these files in one folder, keeping this layout:

```
your-folder/
├── rewrite_posts.py
├── requirements.txt
├── .env.example
└── Prompts/
    └── article.md
```

Open a terminal in that folder and run:

```
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

On Windows, activate the virtual environment with `venv\Scripts\activate` instead.

Next, open `.env` in a text editor and fill it in:

| Setting | What to put |
|---|---|
| `WP_URL` | Your site address, no trailing slash, like `https://yoursite.com` |
| `WP_USER` | Your WordPress login username (not your email) |
| `WP_APP_PASSWORD` | The application password you generated. Spaces are fine |
| `AI_PROVIDER` | `google`, `openrouter`, or `openai` |
| `AI_API_KEY` | Your key from that provider |
| `AI_MODEL` | The model name from that provider's model list |

The `.env` file is the only thing you need to edit to switch providers or models. Keep it private, since it holds your passwords and key.

## Running it

Every time you come back to the project, activate the virtual environment first:

```
source venv/bin/activate
```

### Step 1: dry run

```
python rewrite_posts.py --dry-run --limit 2
```

This writes two sample articles to a `previews/` folder and does **not** touch your site. Open them in a browser and see if you like them. If the style is off (too long, too stiff, too many tables), edit `Prompts/article.md` and run the dry run again.

### Step 2: test one post for real

```
python rewrite_posts.py --limit 1
```

Open that post on your site and make sure the placeholder text is gone and the formatting looks fine in your theme.

### Step 3: do the whole site

```
python rewrite_posts.py
```

Then go make a sandwich. It prints progress as it works through each post.

## Options

| Option | What it does |
|---|---|
| `--dry-run` | Saves previews to `previews/` and changes nothing on your site |
| `--limit N` | Only process N posts |
| `--delay N` | Seconds to wait between posts (default 4). Raise it if a free tier complains about rate limits |
| `--redo` | Ignore the progress file and redo every post |

## Safe to stop and restart

- **Backups:** before changing any post, the program saves the original content to `backups/post-<id>.json`. Delete that folder once you are sure you do not need it.
- **Progress:** finished posts are recorded in `progress.json`. If the run stops (rate limits, a network hiccup, you pressed `Ctrl+C`), run the same command again and it picks up where it left off.
- **Retries:** if the AI call fails or hits a rate limit, the program waits and retries up to 5 times before skipping that post. Skipped posts are listed in the output, and rerunning the program tries them again.

## Customizing the writing

The instructions for the AI live in `Prompts/article.md`, not inside the script. Edit that file to change the length, tone, or structure. The text `{title}` in the file is replaced with each post's title. Run a dry run after each change to see the effect.

Reusing this on another site is easy: change the URL and login in `.env`, adjust the prompt for that site's topic, and run the same three steps.

## Choosing a model

Speed matters more than you would think. One big free model on OpenRouter ran at under 2 tokens per second, which made a single article take forever. A small, fast free model (`nvidia/nemotron-3.5-lightning:free`) ran at over 160 tokens per second and wrote perfectly decent articles. For a job like "write an article from a title," small and fast usually wins.

If a run sits silent for minutes with no output, the model is probably stuck in a queue. Press `Ctrl+C` and switch to a faster one in `.env`. Model names change often, so check your provider's current list.

## Troubleshooting

| Problem | Likely cause |
|---|---|
| `No such file or directory ... Prompts/article.md` | `article.md` is not inside a folder named `Prompts`. Create the folder and move the file into it |
| `Missing ... in your .env file` | A setting in `.env` is blank or misspelled |
| 401 or 403 from WordPress | Wrong username or application password. Use your login username, not your email |
| 404 on the posts URL | Typo in `WP_URL`, or a security plugin is blocking the WordPress REST API |
| AI error 400 or 404 | The model name is wrong for that provider |
| AI error 429 | Free-tier rate limit. The program retries on its own. If it keeps happening, stop and rerun later |
| `SKIPPED: AI returned almost nothing` | The model is too weak or confused. Try a different one |

## What it does not touch

The program only replaces the text of your posts. Demo images, categories, menus, and your Pages (About, Contact, and so on) are left alone, so those may still contain placeholder content.

## The part where you actually do it

Set up the application password. Grab an AI key. Fill in the `.env` file. Run the dry run, then the real thing. Come back to a site full of articles that read like a person wrote them. Your theme still looks great, your site is finally real, and you did not spend another thirty dollars on a plugin.
