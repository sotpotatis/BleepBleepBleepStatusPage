# BleepBleepBleepStatusPage/***StatusPage

> Why are there no status page services that can display everything I want?

-me, 2021.

So, I decided to build something myself. It's called BleepBleepBleep status page since it contains all the @#%&"! stuff that I want it to contain.

BleepBleepBleep takes long to write, so I like to abbreviate it as "***", but that doesn't work for directory paths, so I needed another name. That's where BleepBleepBleep came into my mind.

### Introducing BleepBleepBleep

BleepBleepBleep status page is built using Flask (Python) backend-wise and with Tailwind frontend-wise. It presents a graphical interface to your users, while incident management currently is done via an REST API interface.

### Make it yours!

***StatusPage has the stuff that I want on a status page. Which is, transparent information. A whole lot of information, but accessible.

The best thing is the customizability. I call it "specific but not specific". An example: *** doesn't give you an option like "Plot ping times" when you add a graph for a monitor. It gives you the option to "Plot". Therefore, you can make a monitor plot its RAM usage,
CPU usage, network throughput, or even the amount of caffeine that your engineers have consumed. It is all up to you.

### Quick feature breakdown

Here is a quick feature breakdown.

* Modern and responsive UI based on TailwindCSS.
* Highly configurable using JSON formatted-configuration files, beautifully organized in a way you'll love.
* Plot individual metrics for monitors 
* Automatically change the status of a monitor when it hasn't pinged your server in a grace time.
* REST API where you can set monitor status, upload data to plot, and edit and create incidents.
Authentication using tokens.

### Documentation

Documentation is available at https://statuspagedocs.sweetpotato.online.

### Start here

See the [quickstart](https://statuspagedocs.sweetpotato.online/getting-started/quickstart) page for a tutorial on how to get started right away.
Also, check the directory "integration examples" for some integration examples related to BleepBleepBleepStatusPage.

If you are struggling with anything, open an issue!
