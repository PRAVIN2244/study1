# Module 14: Custom Providers and Advanced Plugin Concepts

## Level: SUPER ADVANCED | Estimated Time: 4 hours

---

## 14.1 How Providers Work Internally

```
┌──────────────────────────────────────────────────────────┐
│                    Terraform Core                        │
│                                                          │
│  ┌──────────┐    gRPC Protocol    ┌──────────────────┐  │
│  │  Config   │◄──────────────────▶│  Provider Plugin  │  │
│  │  Parser   │                    │  (Go binary)      │  │
│  └──────────┘                    │                    │  │
│                                   │  ┌──────────────┐ │  │
│                                   │  │  Schema      │ │  │
│                                   │  │  Definition  │ │  │
│                                   │  ├──────────────┤ │  │
│                                   │  │  CRUD        │ │  │
│                                   │  │  Operations  │ │  │
│                                   │  ├──────────────┤ │  │
│                                   │  │  API Client  │ │  │
│                                   │  └──────────────┘ │  │
│                                   └──────────────────┘  │
└──────────────────────────────────────────────────────────┘
```

### Provider Plugin Protocol

- Terraform Core communicates with providers via **gRPC**
- Providers are separate Go binaries
- Protocol versions: 5 (legacy SDK) and 6 (terraform-plugin-framework)
- Providers implement: GetSchema, Configure, CRUD for each resource

---

## 14.2 Terraform Plugin Framework (Modern Approach)

### Project Structure

```
terraform-provider-example/
├── main.go                    # Entry point
├── go.mod
├── go.sum
├── internal/
│   └── provider/
│       ├── provider.go        # Provider definition
│       ├── resource_server.go # Resource implementation
│       └── data_source_ip.go  # Data source implementation
├── examples/
│   └── main.tf
└── docs/
```

### Provider Definition

```go
// internal/provider/provider.go
package provider

import (
    "context"
    "github.com/hashicorp/terraform-plugin-framework/datasource"
    "github.com/hashicorp/terraform-plugin-framework/provider"
    "github.com/hashicorp/terraform-plugin-framework/provider/schema"
    "github.com/hashicorp/terraform-plugin-framework/resource"
    "github.com/hashicorp/terraform-plugin-framework/types"
)

type ExampleProvider struct {
    version string
}

type ExampleProviderModel struct {
    Endpoint types.String `tfsdk:"endpoint"`
    ApiKey   types.String `tfsdk:"api_key"`
}

func (p *ExampleProvider) Metadata(_ context.Context, _ provider.MetadataRequest, resp *provider.MetadataResponse) {
    resp.TypeName = "example"
    resp.Version = p.version
}

func (p *ExampleProvider) Schema(_ context.Context, _ provider.SchemaRequest, resp *provider.SchemaResponse) {
    resp.Schema = schema.Schema{
        Attributes: map[string]schema.Attribute{
            "endpoint": schema.StringAttribute{
                Optional:    true,
                Description: "API endpoint URL",
            },
            "api_key": schema.StringAttribute{
                Optional:    true,
                Sensitive:   true,
                Description: "API authentication key",
            },
        },
    }
}

func (p *ExampleProvider) Configure(ctx context.Context, req provider.ConfigureRequest, resp *provider.ConfigureResponse) {
    var config ExampleProviderModel
    resp.Diagnostics.Append(req.Config.Get(ctx, &config)...)
    if resp.Diagnostics.HasError() {
        return
    }

    // Create API client and make it available to resources
    client := NewAPIClient(config.Endpoint.ValueString(), config.ApiKey.ValueString())
    resp.DataSourceData = client
    resp.ResourceData = client
}

func (p *ExampleProvider) Resources(_ context.Context) []func() resource.Resource {
    return []func() resource.Resource{
        NewServerResource,
    }
}

func (p *ExampleProvider) DataSources(_ context.Context) []func() datasource.DataSource {
    return []func() datasource.DataSource{
        NewIPDataSource,
    }
}

func New(version string) func() provider.Provider {
    return func() provider.Provider {
        return &ExampleProvider{version: version}
    }
}
```

### Resource Implementation

```go
// internal/provider/resource_server.go
package provider

import (
    "context"
    "github.com/hashicorp/terraform-plugin-framework/resource"
    "github.com/hashicorp/terraform-plugin-framework/resource/schema"
    "github.com/hashicorp/terraform-plugin-framework/types"
)

type ServerResource struct {
    client *APIClient
}

type ServerResourceModel struct {
    ID           types.String `tfsdk:"id"`
    Name         types.String `tfsdk:"name"`
    Size         types.String `tfsdk:"size"`
    Region       types.String `tfsdk:"region"`
    IPAddress    types.String `tfsdk:"ip_address"`
    Status       types.String `tfsdk:"status"`
}

func NewServerResource() resource.Resource {
    return &ServerResource{}
}

func (r *ServerResource) Metadata(_ context.Context, req resource.MetadataRequest, resp *resource.MetadataResponse) {
    resp.TypeName = req.ProviderTypeName + "_server"
}

func (r *ServerResource) Schema(_ context.Context, _ resource.SchemaRequest, resp *resource.SchemaResponse) {
    resp.Schema = schema.Schema{
        Description: "Manages a server instance.",
        Attributes: map[string]schema.Attribute{
            "id": schema.StringAttribute{
                Computed:    true,
                Description: "Server identifier",
            },
            "name": schema.StringAttribute{
                Required:    true,
                Description: "Server name",
            },
            "size": schema.StringAttribute{
                Required:    true,
                Description: "Server size (small, medium, large)",
            },
            "region": schema.StringAttribute{
                Required:    true,
                Description: "Deployment region",
            },
            "ip_address": schema.StringAttribute{
                Computed:    true,
                Description: "Assigned IP address",
            },
            "status": schema.StringAttribute{
                Computed:    true,
                Description: "Current server status",
            },
        },
    }
}

func (r *ServerResource) Configure(_ context.Context, req resource.ConfigureRequest, resp *resource.ConfigureResponse) {
    if req.ProviderData == nil {
        return
    }
    r.client = req.ProviderData.(*APIClient)
}

func (r *ServerResource) Create(ctx context.Context, req resource.CreateRequest, resp *resource.CreateResponse) {
    var plan ServerResourceModel
    resp.Diagnostics.Append(req.Plan.Get(ctx, &plan)...)
    if resp.Diagnostics.HasError() {
        return
    }

    // Call API to create server
    server, err := r.client.CreateServer(plan.Name.ValueString(), plan.Size.ValueString(), plan.Region.ValueString())
    if err != nil {
        resp.Diagnostics.AddError("Error creating server", err.Error())
        return
    }

    // Map response to state
    plan.ID = types.StringValue(server.ID)
    plan.IPAddress = types.StringValue(server.IPAddress)
    plan.Status = types.StringValue(server.Status)

    resp.Diagnostics.Append(resp.State.Set(ctx, plan)...)
}

func (r *ServerResource) Read(ctx context.Context, req resource.ReadRequest, resp *resource.ReadResponse) {
    var state ServerResourceModel
    resp.Diagnostics.Append(req.State.Get(ctx, &state)...)
    if resp.Diagnostics.HasError() {
        return
    }

    server, err := r.client.GetServer(state.ID.ValueString())
    if err != nil {
        resp.Diagnostics.AddError("Error reading server", err.Error())
        return
    }

    state.Name = types.StringValue(server.Name)
    state.Size = types.StringValue(server.Size)
    state.Region = types.StringValue(server.Region)
    state.IPAddress = types.StringValue(server.IPAddress)
    state.Status = types.StringValue(server.Status)

    resp.Diagnostics.Append(resp.State.Set(ctx, state)...)
}

func (r *ServerResource) Update(ctx context.Context, req resource.UpdateRequest, resp *resource.UpdateResponse) {
    var plan ServerResourceModel
    resp.Diagnostics.Append(req.Plan.Get(ctx, &plan)...)
    if resp.Diagnostics.HasError() {
        return
    }

    var state ServerResourceModel
    resp.Diagnostics.Append(req.State.Get(ctx, &state)...)

    server, err := r.client.UpdateServer(state.ID.ValueString(), plan.Name.ValueString(), plan.Size.ValueString())
    if err != nil {
        resp.Diagnostics.AddError("Error updating server", err.Error())
        return
    }

    plan.ID = state.ID
    plan.IPAddress = types.StringValue(server.IPAddress)
    plan.Status = types.StringValue(server.Status)

    resp.Diagnostics.Append(resp.State.Set(ctx, plan)...)
}

func (r *ServerResource) Delete(ctx context.Context, req resource.DeleteRequest, resp *resource.DeleteResponse) {
    var state ServerResourceModel
    resp.Diagnostics.Append(req.State.Get(ctx, &state)...)
    if resp.Diagnostics.HasError() {
        return
    }

    err := r.client.DeleteServer(state.ID.ValueString())
    if err != nil {
        resp.Diagnostics.AddError("Error deleting server", err.Error())
        return
    }
}
```

### Main Entry Point

```go
// main.go
package main

import (
    "context"
    "flag"
    "log"

    "github.com/hashicorp/terraform-plugin-framework/providerserver"
    "terraform-provider-example/internal/provider"
)

var version = "dev"

func main() {
    var debug bool
    flag.BoolVar(&debug, "debug", false, "set to true to run the provider with support for debuggers")
    flag.Parse()

    opts := providerserver.ServeOpts{
        Address: "registry.terraform.io/myorg/example",
        Debug:   debug,
    }

    err := providerserver.Serve(context.Background(), provider.New(version), opts)
    if err != nil {
        log.Fatal(err.Error())
    }
}
```

---

## 14.3 Using a Local Custom Provider

### Development Override

```hcl
# ~/.terraformrc (or %APPDATA%/terraform.rc on Windows)
provider_installation {
  dev_overrides {
    "myorg/example" = "/home/user/go/bin"
  }
  direct {}
}
```

### Usage

```hcl
terraform {
  required_providers {
    example = {
      source = "myorg/example"
    }
  }
}

provider "example" {
  endpoint = "https://api.example.com"
  api_key  = var.api_key
}

resource "example_server" "web" {
  name   = "web-server"
  size   = "medium"
  region = "us-east"
}

output "server_ip" {
  value = example_server.web.ip_address
}
```

---

## 14.4 Publishing a Provider

### To the Terraform Registry

```bash
# 1. Create a GitHub release
git tag v1.0.0
git push origin v1.0.0

# 2. Use GoReleaser to build binaries
goreleaser release --clean

# 3. Sign with GPG key registered at registry.terraform.io

# 4. Provider appears at:
# registry.terraform.io/myorg/example
```

### Required Repository Naming

```
terraform-provider-<NAME>
# Example: terraform-provider-example
```

---

## 14.5 External Data Source (Simpler Alternative)

For simple integrations, use the `external` data source instead of building a full provider:

```hcl
data "external" "ip_info" {
  program = ["python3", "${path.module}/scripts/get_ip_info.py"]

  query = {
    ip_address = "8.8.8.8"
  }
}

output "ip_info" {
  value = data.external.ip_info.result
  # → { "city" = "Mountain View", "country" = "US", "org" = "Google" }
}
```

```python
# scripts/get_ip_info.py
import json
import sys
import urllib.request

input_data = json.load(sys.stdin)
ip = input_data["ip_address"]

response = urllib.request.urlopen(f"https://ipinfo.io/{ip}/json")
data = json.loads(response.read())

output = {
    "city": data.get("city", ""),
    "country": data.get("country", ""),
    "org": data.get("org", ""),
}

print(json.dumps(output))
```

### Rules for External Data Source Scripts

1. Read JSON from stdin
2. Write JSON to stdout
3. All values must be strings
4. Exit code 0 = success, non-zero = error
5. Error messages go to stderr

---

## 14.6 terraform-plugin-mux (Combining SDKs)

When migrating from SDKv2 to Framework, you can serve both simultaneously:

```go
func main() {
    ctx := context.Background()

    // SDKv2 provider (legacy resources)
    sdkv2Provider := sdkv2provider.Provider()

    // Framework provider (new resources)
    frameworkProvider := frameworkprovider.New()

    // Combine both
    muxServer, err := tf5to6server.UpgradeServer(
        ctx,
        sdkv2Provider.GRPCProvider,
    )

    providers := []func() tfprotov6.ProviderServer{
        providerserver.NewProtocol6(frameworkProvider),
        func() tfprotov6.ProviderServer { return muxServer },
    }

    muxServer, err := tf6muxserver.NewMuxServer(ctx, providers...)
    // ...
}
```

---

## Exercises

### Exercise 14.1: External Data Source
Create an external data source script that:
1. Accepts a domain name as input
2. Performs a DNS lookup
3. Returns the IP addresses as JSON

### Exercise 14.2: Study a Provider
Clone the `terraform-provider-aws` repository and study:
1. How a simple resource (like `aws_s3_bucket`) is implemented
2. The schema definition
3. The CRUD operations

### Exercise 14.3: Build a Provider (Advanced)
Build a minimal custom provider that manages a local JSON file as a "resource" (create, read, update, delete entries in the file).

---

## Key Takeaways

- Providers are Go binaries communicating with Terraform Core via gRPC
- The terraform-plugin-framework is the modern way to build providers
- Each resource implements Create, Read, Update, Delete operations
- Use `dev_overrides` in `.terraformrc` for local development
- The `external` data source is a simpler alternative for read-only integrations
- Provider names must follow `terraform-provider-<NAME>` convention
- Publishing requires GitHub releases, GoReleaser, and GPG signing

---

## Official Documentation Links

| Topic | Link |
|-------|------|
| Plugin Development Overview | [developer.hashicorp.com/terraform/plugin](https://developer.hashicorp.com/terraform/plugin) |
| Terraform Plugin Framework | [developer.hashicorp.com/terraform/plugin/framework](https://developer.hashicorp.com/terraform/plugin/framework) |
| Plugin Framework — Getting Started | [developer.hashicorp.com/terraform/tutorials/providers-plugin-framework](https://developer.hashicorp.com/terraform/tutorials/providers-plugin-framework) |
| Plugin Protocol | [developer.hashicorp.com/terraform/plugin/how-terraform-works](https://developer.hashicorp.com/terraform/plugin/how-terraform-works) |
| Provider Resources (Framework) | [developer.hashicorp.com/terraform/plugin/framework/resources](https://developer.hashicorp.com/terraform/plugin/framework/resources) |
| Provider Data Sources (Framework) | [developer.hashicorp.com/terraform/plugin/framework/data-sources](https://developer.hashicorp.com/terraform/plugin/framework/data-sources) |
| Provider Schema (Framework) | [developer.hashicorp.com/terraform/plugin/framework/handling-data/schemas](https://developer.hashicorp.com/terraform/plugin/framework/handling-data/schemas) |
| Publishing Providers | [developer.hashicorp.com/terraform/registry/providers/publishing](https://developer.hashicorp.com/terraform/registry/providers/publishing) |
| `external` Data Source | [registry.terraform.io/providers/hashicorp/external/latest/docs/data-sources/external](https://registry.terraform.io/providers/hashicorp/external/latest/docs/data-sources/external) |
| Plugin Mux | [developer.hashicorp.com/terraform/plugin/mux](https://developer.hashicorp.com/terraform/plugin/mux) |
| Terraform Plugin SDKv2 (Legacy) | [developer.hashicorp.com/terraform/plugin/sdkv2](https://developer.hashicorp.com/terraform/plugin/sdkv2) |
| Dev Overrides (Local Testing) | [developer.hashicorp.com/terraform/cli/config/config-file#development-overrides-for-provider-developers](https://developer.hashicorp.com/terraform/cli/config/config-file#development-overrides-for-provider-developers) |

---

[← Previous Module](../module-13-expressions-and-functions/README.md) | [Next Module: Testing and Validation →](../module-15-testing-and-validation/README.md)
