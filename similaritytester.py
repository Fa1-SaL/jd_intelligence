from openai import OpenAI

client = OpenAI(api_key="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")

text = """Software Expert (CAD and Engineering)
Hourly contract
Remote
Recent hire 1Recent hire 2Recent hire 3
118 hired this month

$0-$100
per hour
Mercor logo
Posted by Mercor
mercor.com





Location: Remote (must have access to a physical Mac)

Fluent Language Skills Required: English

Why This Role Exists

Mercor is supporting a high-priority data collection initiative aimed at improving how AI systems understand complex software interfaces and real-world, multi-step workflows. Current datasets lack the fidelity and expert grounding needed to reflect authentic professional software usage. This project addresses that gap by collecting high-quality screen annotations and screen recordings performed by experienced domain experts working in real digital environments.

What You’ll Do

Depending on the task phase, you may be asked to complete one or both of the following:

Record screen sessions demonstrating specific tasks, accompanied by clear verbal narration explaining each step

Annotate screenshots of professional software by drawing precise bounding boxes around relevant UI elements

Follow provided staging instructions to set up specific UI states prior to recording

Use a custom capture tool to record workflows accurately and consistently

Adhere closely to task guidelines to ensure data quality and usability

Who You Are

You have strong familiarity with professional software tools used in your domain including:

AutoCAD Mechanical

SolidWorks

Inventor

Vivado

You are detail-oriented and capable of following precise instructions

You are comfortable working independently and meeting tight deadlines

You have access to a physical Mac and can create a fresh macOS user profile if required

Nice-to-Have

Prior experience with data collection, annotation, or QA work

Experience recording or documenting workflows

Comfort working with new tools and staged environments

What Success Looks Like

Screen annotations are precise, consistent, and aligned with guidelines

Screen recordings accurately capture realistic, expert workflows

Tasks are completed efficiently while maintaining high quality

Collected data is usable at scale for downstream AI research and development

We consider all qualified applicants without regard to legally protected characteristics and provide reasonable accommodations upon request."""

response = client.embeddings.create(
    model="text-embedding-3-small",
    input=text,
    dimensions=1536
)

embedding = response.data[0].embedding

print(embedding)