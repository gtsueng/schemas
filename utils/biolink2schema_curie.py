import yaml
from jsonschema import validate, ValidationError
import json


# schema for biolink classes, used for json schema validation
BIOLINK_CLASS_SCHEMA = {
    "type": "object",
    "properties": {
        "is_a": {"type": "string"},
        "description": {"type": "string"},
    },
    "required": ["is_a"]
}

# schema for biolink slots, used for json schema validation
BIOLINK_SLOT_SCHEMA = {
    "type": "object",
    "properties": {
        "is_a": {"type": "string"},
        "description": {"type": "string"},
        "domain": {"type": "string"},
        "range": {"type": "string"}
    },
    "required": ["domain", "range"]
}


def capitalizeClassName(class_name):
    """Concatenate Words and Capitalize the first character of each word

    Example: biological entity (input)  --- >  BiologicalEntity (output)

    Keyword arguments:
    class_name: input class name, e.g. biological entity
    """
    return ''.join([_word.capitalize() for _word in class_name.split(' ')])


def capitalizePropertyName(property_name):
    """Concatenate Words and Capitalize the first character of all words excpet the first one

    Example: strength unit (input)  ---- >. strengthUnit (output)

    Keyword arguments:
    property_name: input property name, e.g. interacts with
    """
    capitalized =  ''.join([_word.capitalize() for _word in property_name.split(' ')])
    return capitalized[0].lower() + capitalized[1:]


def convert_class(file_name):
    """Convert all classes in BioLink model into Schema.org compatible format
    """
    with open(file_name) as f:
        restruct_classes = []
        doc = yaml.load(f)
        classes = doc['classes']
        for k, v in classes.items():
            try:
                validate(v, BIOLINK_CLASS_SCHEMA)
            except ValidationError:
                print(k, v)
                continue
            # some classes may lack description
            description = None
            if "description" in v:
                description = v["description"]
            # remove classes that belongs to either "association" or
            # "attribute", e.g. "genetovariantassociation"
            suffix_to_remove = ["quantifier", "qualifiers", "qualifier",
                                "association", "relationship"]
            if v["is_a"] not in ["association", "attribute",
                                 "biological sex",
                                 "administrative entity"] and not v["is_a"].endswith(tuple(suffix_to_remove)):
                restruct_class = {"rdfs:label": capitalizeClassName(k),
                                  "@id": "bts:" + capitalizeClassName(k),
                                  "@type": "rdfs:Class",
                                  "rdfs:subClassOf": {"@id": "bts:" + capitalizeClassName(v['is_a'])},
                                  "schema:isPartOf": {"@id": "http://schema.biothings.io"},
                                  "rdfs:comment": description}
                if v["is_a"] == "named thing":
                    restruct_class["rdfs:subClassOf"]["@id"] = "schema:Thing"
                restruct_classes.append(restruct_class)
    return restruct_classes


def convert_properties(file_name):
    """Convert all slots in BioLink model into Schema.org properties
    file_name: biolink data model yaml file
    """
    with open(file_name) as f:
        restruct_properties = []
        doc = yaml.load(f)
        slots = doc['slots']
        for k, v in slots.items():
            try:
                validate(v, BIOLINK_SLOT_SCHEMA)
            except ValidationError:
                print(k, v)
                continue
            # some slots may lack description
            description = None
            if "description" in v:
                description = v["description"]
            if v["domain"] not in ['named thing', 'association', 'thing with taxon']:
                restruct_property = {"rdfs:label": capitalizePropertyName(k),
                                     "rdfs:comment": description,
                                     "schema:domainIncludes": {"@id": "bts:" + capitalizeClassName(v["domain"])},
                                     "schema:rangeIncludes": {"@id": "bts:" + capitalizeClassName(v["range"])},
                                     "@id": "bts:" + capitalizePropertyName(k),
                                     "@type": "rdf:Property",
                                     "schema:isPartOf": {"@id": "http://schema.biothings.io"}}
                if v["domain"] == "named thing":
                    restruct_property["schema:domainIncludes"] = {"@id": "schema:Thing"}
                if v["range"] == "named thing":
                    restruct_property["schema:rangeIncludes"] = {"@id": "schema:Thing"}
                if v["range"] == "phenotype":
                    restruct_property["schema:rangeIncludes"] = {"@id": "bts:DiseaseOrPhenotypicFeature"}
                restruct_properties.append(restruct_property)
    return restruct_properties

def convert_biolink_model_to_schema(file_name):
    classes = convert_class(file_name)
    properties = convert_properties(file_name)
    graph = classes + properties
    biothings_schema = {"@id": "http://schema.biothings.io/#0.1",
                        "@context": {"rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
                                     "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
                                     "xsd": "http://www.w3.org/2001/XMLSchema#",
                                     "bts": "http://schema.biothings.io/",
                                     "schema": "http://schema.org/"},
                        "@graph": graph}
    return biothings_schema

if __name__ == "__main__":
    with open("../biothings/biothings_curie.jsonld", "w") as outfile:
        json.dump(convert_biolink_model_to_schema("../biolink/biolink_model.yaml"), outfile, sort_keys = True, indent = 4,
               ensure_ascii = False)