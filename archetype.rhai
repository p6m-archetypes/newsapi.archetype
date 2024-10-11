let context = #{};

// Pass `-s debug-answers` to archetect to output the answers it sees from various sources
if switch_enabled("debug-answers") {
    print("Answers:");
    print(as_yaml(ANSWERS));
    print();
}

context += prompt("Org Name:", "org-name", #{
    help: "Examples: p6m, nalix, launch321",
    placeholder: "p6m",
    cases: [
        CasedIdentityCasedValue(PROGRAMMING_CASES),
        FixedKeyCasedValue("org-title", TitleCase),
    ],
});

context += prompt("Solution Name:", "solution-name", #{
    help: "Examples: watercolor, pearson, link",
    placeholder: "data-platform",
    cases: [
        CasedIdentityCasedValue(PROGRAMMING_CASES),
        FixedKeyCasedValue("solution-title", TitleCase),
    ],
});

context += prompt("Project Prefix:", "project-prefix", #{
    cases: [
        CasedIdentityCasedValue(PROGRAMMING_CASES),
    ],
});

context+= prompt("Project Suffix:", "project-suffix", #{
    type: Select([
        "Driver",
        "Data Adapter",
    ]),
    cases: [
        CasedIdentityCasedValue(PROGRAMMING_CASES),
    ],
});


context += set("project-name", render("{{ project-prefix }}-{{ project-suffix }}", context), #{
    cases: [
        CasedIdentityCasedValue(PROGRAMMING_CASES),
        FixedKeyCasedValue("project-title", TitleCase),
    ],
});

context += prompt("Project Author:", "author_full", #{
    placeholder: "Your Name <your.name@example.com>",
});

context += prompt("Packages:", "packages", #{
    defaults_with: ["newsapi"],
    type: List,
    cases: [
        CasedKeyCasedValue("package-name", PROGRAMMING_CASES),
        FixedKeyCasedValue("package-title", TitleCase),
    ],
});

context += prompt("Features:", "features", #{
    type: MultiSelect([
      "NewsAPI",
    ]),
});

// Pass `-s debug-context` to archetect to output the context 
if switch_enabled("debug-context") {
    print("Context:");
    print(as_yaml(context));
    print();
}

context["github-artifactory_username"] = "${{ secrets.ARTIFACTORY_USERNAME }}";
context["github-artifactory_id_token"] = "${{ secrets.ARTIFACTORY_IDENTITY_TOKEN }}";

render(Directory("contents/base"), context);

for item in context.packages {
    render(Directory("contents/package"), context + item);
}


context

