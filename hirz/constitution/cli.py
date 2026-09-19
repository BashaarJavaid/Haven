"""Database-free constitution workflows with JSON stdout."""

import argparse
import json
import sys

import yaml
from pydantic import ValidationError

from hirz.constitution.boundary import BoundaryError, Dogwood
from hirz.constitution.compiler import compile_policy
from hirz.constitution.preview import preview
from hirz.constitution.render import render
from hirz.constitution.schema import load
from hirz.graph.models import GraphError


async def constitution_command(args: argparse.Namespace) -> int:
    try:
        if args.operation == "preview":
            result = preview(load(args.old), load(args.new))
        else:
            policy = load(args.file)
            compiled = compile_policy(policy, args.gateway_resource)
            validation = await Dogwood().validate(compiled)
            result = {
                "valid": True,
                "version": policy.version,
                "household": policy.household,
                "analysis": "not analyzed: local mode",
                "engine": "dogwood-local",
                "validation": validation,
                "english": render(policy),
            }
            if args.operation == "compile":
                result.update(
                    policy=compiled.policy,
                    schema=compiled.schema,
                    manifest=compiled.manifest,
                )
        print(json.dumps(result))
        return 0
    except ValidationError as exc:
        # Never echo input values in validation diagnostics.
        errors = [
            {"path": ".".join(map(str, e["loc"])), "message": e["msg"]}
            for e in exc.errors(include_input=False, include_url=False)
        ]
        print(
            json.dumps({"error": "INVALID_CONSTITUTION", "details": errors}),
            file=sys.stderr,
        )
    except (OSError, ValueError, yaml.YAMLError, GraphError, BoundaryError) as exc:
        print(
            json.dumps({"error": "CONSTITUTION_ERROR", "message": str(exc)}),
            file=sys.stderr,
        )
    return 1
