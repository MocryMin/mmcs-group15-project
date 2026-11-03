# Original project-launch transcript excerpts

Source: the transcript export supplied by Mocry, associated with the 26 October 2026 project-launch class. Selected complete timestamped segments below are reproduced verbatim from that export. They have not been checked against audio; speech repetitions and transcription errors are preserved. Speaker 0 is the lecturer in these selected segments. These are excerpts, not the complete recording.

Interpretations and the separately reported after-class discussion are in [TEACHER_CLARIFICATIONS.md](TEACHER_CLARIFICATIONS.md).

## EX-01 — 01:05:51.449 - 01:06:49.469

Source label: Speaker 0.

> and work on uh the project again in your groups, OK. Uh, if you're in different workshop hours to your groups, um, that's OK. It would be better if you guys could come to the same workshop. OK. So whether that's the first hour or the second hour, um, whatever suits your schedule best, uh, or you can stay there for the full 2 hours, whatever you like. OK. Um Then the final report that you submit, OK? So as Carl mentioned, this is technical report. OK. So here, we want to see all of the technical details of everything that you've done. And this has a 10-page limit. OK, so it's not long. OK. So you need to be smart about what's relevant and not what's not relevant. OK. Then the presentation that you deliver in week 11, OK? So this will be graded by myself and Kal and

## EX-02 — 01:06:49.469 - 01:07:45.520

Source label: Speaker 0.

> please note this is not a technical presentation. OK, this is a business pitch. OK. In past, in the past, I say every year, if you include your mathematical formulation or as Carl commented, code snippets, you will fail. OK, this is a non-negotiable. OK. And every year, students still do it. And some of you are gonna do it again this year, I'm almost certain. OK, so please, no code, no maths, no maths in your final, it's a business presentation. OK. You need to somehow convince the CEO that he or she is really smart and they understand all of this maths that you did without seeing it. OK. So please, very, very important on that. OK. A few things uh about logistics.

## EX-03 — 01:09:38.757 - 01:10:26.830

Source label: Speaker 0.

> Where Uh, on the Y axis or the data points is the total, let's say, megawatts of energy generated in the UK on any given day, OK? So that may look They may look something like this. OK, so this would be generation. OK, fine. OK. But then, so what I've also given you is uh energy demand, OK? And this is the megawatts of energy demanded in the UK on any given day, OK? And this may look something like this.

## EX-04 — 01:11:32.220 - 01:12:27.259

Source label: Speaker 0.

> OK. So this is on a UK wide scale. OK. And this is a bad assumption to make, OK, that this is how we should deal with the mismatch in energy demand, and I'll explain that for a few, uh a bit later. OK. Um, then the final thing I've given you is energy generation from a wind farm. OK. So where I got this data from is I, uh, look, so there's like a web page where it tells you energy projects that are, uh, commissioned. OK. So they give you the location, the number of turbines, the rating of the turbines, and things like that. And so what I did is I fetched weather data, um, From online. And then I used the weather data together with the, let's say the characteristics of a wind farm that's to be developed. And I simulated what the energy generation would have been,

## EX-05 — 01:12:27.709 - 01:13:24.490

Source label: Speaker 0.

> assuming that things don't fail and there's no maintenance and blah, blah, blah. OK. So that gives you some kind of Energy generation. OK. OK. And now. The baseline model, OK, we should think of this as something purely deterministic. OK. So we know exactly in the future. We know exactly the difference between generation and demand. We know exactly what we're gonna produce in the future. And sorry, what I've also given you is I've given you the price. So you also have like pond. Oh, I don't know how to draw a pound symbol, but anyways. A pound per megawatt. OK, let's look at something like that. OK. So you know exactly in the future. How much of this energy you can sell on the

## EX-06 — 01:13:24.490 - 01:14:23.089

Source label: Speaker 0.

> open market, and how much you can sell it for. OK. So, that's kind of a straightforward task, right? Because you can just look at the, the amount of energy I can sell. Do I, I take the maximum, no, the minimum of what I can sell and what I can produce, and I multiply it by the price. OK, that's very straightforward. But now, we have some extra things that we can do. OK. So at the start of time, well, at T0, uh, I can decide to install batteries, OK? Or I can, uh, let's say, set up infrastructure that I can use to produce hydrogen. OK. If, if I make the investment decision, OK, and you can even make this a temporal investment decision. So it's not like you have to do it here, maybe you can also Installed another battery here and another

## EX-07 — 01:14:23.089 - 01:15:17.979

Source label: Speaker 0.

> battery there, or, or something, I don't know, depending on how you wanna model it. But anyways, so what happens now is, if I decide to install a battery, OK, I've got some battery. And this battery I can use to store energy. OK. So on every day, I know. My generation, OK, so I know how much my farm produces. Now I need to decide. With what do I do with this energy? Do I use it to charge my battery? OK. Or do I sell it on the open market at the current price, if obviously I can sell it on the open market. OK. But I also need to decide in each time period what do I do with my battery. OK, cause maybe I'm not going to charge it, maybe I'm going to discharge. OK.

## EX-08 — 01:15:18.100 - 01:16:13.919

Source label: Speaker 0.

> And when I discharge, I'm basically throwing energy out of the battery and I'm selling it on the open market. So this battery is useful for two reasons, OK. The first reason is because when we produce more than demand, we don't throw it away, we store it. OK. The second reason it's useful is because when prices are low, We can decide not to sell the energy on the market and rather store it in the battery so that we can sell it later when prices are high. OK. The other option is, other than batteries, is to produce hydrogen. OK So, again, you now have some energy. You can decide to use it to produce hydrogen or charge batteries. OK? If you produce hydrogen, You, the easy assumption would be

## EX-09 — 01:16:13.919 - 01:17:11.689

Source label: Speaker 0.

> to just sell it on the open market. OK, so just assume you can always sell like 1 kg of hydrogen for, I don't know, 2 pounds 50 or whatever it is, OK. The other option is to say, well, OK, we can decide to set up hydrogen production infrastructure, but we can also set up hydrogen energy generation infrastructure. OK. So this means if I produce hydrogen, I can store it. OK. And then later when the price is high or when I can sell a lot of energy on the market, I can burn this hydrogen and then produce more energy. OK, so, yeah, it's, it's up to you guys how you want to model it and what kind of detail you want to model. OK. Um, so this is kind of what we mean by like the vanilla or the baseline model. OK, I think it's, in my opinion, it's really well scoped. And it's very like, there's just something here that you

## EX-10 — 01:18:07.060 - 01:19:02.209

Source label: Speaker 0.

> from them in the future. OK, so you can think of this as we talk about the language of our modeling, it's like kind of a, in a way a two-stage, it was actually multi-stage, but think of it as like a two-stage stochastic programming problem where your first stage decision is. OK, this is my uh investment decision. I install batteries, OK. And now I have many scenarios of energy generation and uh energy like sales prices and whatever and then I solve the model in all of those scenarios. OK. The other approach, the other thing that, and the other thing that you can investigate or decide to go down is. OK, we're fixed with our infrastructure. OK. So I have a battery and I have some kind of battery capacity. OK. But now on each day. I know what the energy generation is and I know the demand of each day.

## EX-11 — 01:19:03.540 - 01:19:59.759

Source label: Speaker 0.

> OK. But I don't know the price and I don't know the energy generation, and I don't know the demand in the future. I know nothing about the future. OK What do I do with this energy? OK, so I can sell it on the open market today, and I know exactly how much money I get. OK. Or I can take a risk and say, I'm gonna store it. Because maybe the price of the energy is gonna cost more, or, well, I could sell it for more in the future. OK, but how do you know, like, on the flip side, you could keep it and then in the future it could cost less. So then you actually made a net loss. Well, not a net loss, but like an opportunity cost loss. OK. So, yeah, so those are the, the two sub-problems. I don't think you should do all three things. Rather pick one of these like investment with uncertainty or

## EX-12 — 01:22:48.270 - 01:23:44.109

Source label: Speaker 0.

> OK. So, This is why this energy flexibility becomes quite important because actually we wouldn't really necessarily install batteries at the wind farm itself, but maybe we'll do it like somewhere here in England. Um, but, yeah. OK. So, for the project, the data I've given you is essentially just assuming that the demand, like we ignore the effects of the grid. And we just say, well, OK, well, anywhere there's demand, if we have generation somewhere in the UK we can get it there. OK. If you would like to think about the restrictions that the grid itself has. You're also more than welcome to go down that route. OK, I'm not an expert in this. But I'm happy to figure it out with you, OK. Um So Yeah, that's uh all I have to say. OK, so.

