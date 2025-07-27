# Our Approach: Thinking Like a Real Travel Planner

For this challenge, we realized that just finding documents with the right keywords wasn't enough. A real travel plan isn't just a list of random facts; it's a step-by-step guide. So, we built our solution to think like a human travel planner would. It works in two simple stages: first, it makes the high-level plan, and then it fills in the nitty-gritty details.

### Stage 1: Building the Main Itinerary

First things first, we figure out the main parts of the trip. This is for the `extracted_sections` part of the output. Instead of one big, confusing search, we ask a series of simple questions, just like you would when planning a vacation:

1.  "Okay, where should we even go?"
2.  "What's there to do by the coast?"
3.  "What kind of food should we try?"
4.  "What do we need to pack?"
5.  "Where's the fun nightlife?"

To get the best answers, we made the system smart enough to look in the right place. For the "Cities" question, it looks only in the `Cities.pdf`. For "Nightlife," it checks the `Things to Do.pdf`. This common-sense approach means we get the right info every time. We use a powerful AI model (`all-mpnet-base-v2`) to find the single best paragraph that answers each question.

### Stage 2: Filling in the Details

Once we have our main plan, we go back to fill in the details for the `subsection_analysis`. This is the most important part. For each of the top 5 sections we found, our system does a second, deeper dive.

It reads through that section and intelligently breaks it down into smaller, more specific topics. For example, when it looks at the "Coastal Adventures" section, it knows to pull out "Beach Hopping" and "Water Sports" as two separate, detailed points. This way, the final output isn't just a big block of text, but a well-organized and genuinely useful travel plan, with all the key details clearly laid out.
